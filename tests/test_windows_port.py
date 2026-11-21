"""Windows runtime regressions; run on macOS/Linux with mocked Win32 APIs.

These tests do not claim to replace a live Windows Terminal/MP3 test.
"""
import ctypes
import io
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from arcana import tui, music
from play import Controller


class WindowsPortTests(unittest.TestCase):
    def test_windows_key_mapping_including_wasd(self):
        term = tui.RawTerminal()
        cases = [
            (('\xe0','H'), 'UP'), (('\xe0','P'), 'DOWN'),
            (('\xe0','K'), 'LEFT'), (('\xe0','M'), 'RIGHT'),
            (('\x00','H'), 'UP'), (('\r',), 'ENTER'),
            (('\x1b',), 'ESC'), (('\x08',), 'BACKSPACE'),
            (('w',), 'w'), (('s',), 's'), (('a',), 'a'),
            (('d',), 'd'), (('中',), '中'),
        ]
        for chars, expected in cases:
            with self.subTest(chars=chars), patch.object(tui.os,'name','nt'), patch.object(tui,'msvcrt',create=True) as fake:
                fake.getwch.side_effect = list(chars)
                self.assertEqual(term.read(), [expected])
        with patch.object(tui.os,'name','nt'), patch.object(tui,'msvcrt',create=True) as fake:
            fake.getwch.side_effect = ['\xe0','Q']
            self.assertEqual(term.read(),[])

    def test_windows_console_enters_vt_and_restores_after_exit_escape(self):
        output = io.StringIO()
        calls=[]
        kernel=Mock()
        kernel.GetStdHandle.return_value=123
        def read_mode(handle,ptr):
            ctypes.cast(ptr,ctypes.POINTER(ctypes.c_uint32)).contents.value=0x0003
            return 1
        kernel.GetConsoleMode.side_effect=read_mode
        def write_mode(handle,mode):
            calls.append(('mode',mode))
            return 1
        kernel.SetConsoleMode.side_effect=write_mode
        class LogWriter(io.StringIO):
            def write(self,s):
                calls.append(('out',s))
                return super().write(s)
        output=LogWriter()
        with patch.object(tui.os,'name','nt'),patch('ctypes.WinDLL',return_value=kernel,create=True),patch.object(tui.sys,'stdout',output):
            with tui.RawTerminal():
                self.assertIn(('mode',0x000F), calls)
            self.assertEqual(calls[-1],('mode',0x0003))
            last_cleanup=next(i for i,(typ,val) in enumerate(calls) if typ=='out' and '\x1b[?1049l' in val)
            self.assertLess(last_cleanup,len(calls)-1)
        self.assertIn('\x1b[?1049h',output.getvalue())
        self.assertIn('\x1b[?1049l',output.getvalue())

    def test_windows_unsupported_vt_fails_before_drawing(self):
        kernel=Mock()
        kernel.GetStdHandle.return_value=123
        def read_mode(handle,ptr):
            ctypes.cast(ptr,ctypes.POINTER(ctypes.c_uint32)).contents.value=3
            return 1
        kernel.GetConsoleMode.side_effect=read_mode
        kernel.SetConsoleMode.return_value=0
        output=io.StringIO()
        with patch.object(tui.os,'name','nt'),patch('ctypes.WinDLL',return_value=kernel,create=True),patch.object(tui.sys,'stdout',output):
            with self.assertRaisesRegex(RuntimeError,'Windows Terminal'):
                with tui.RawTerminal():pass
        self.assertNotIn('\x1b[?1049h',output.getvalue())

    def test_windows_audio_command_uses_uploaded_tracks_and_no_console_popup(self):
        with patch.object(music.os,'name','nt'),patch.object(music.shutil,'which',return_value=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'):
            player=music.Music()
            self.assertTrue(player.available)
            player.scene='shop'
            fake_proc=Mock()
            fake_proc.poll.return_value=0
            fake_proc.wait.return_value=0
            fake_proc.returncode=0
            seen=[]
            def create(cmd,**kwargs):
                seen.append((cmd,kwargs))
                player._stop.set()
                return fake_proc
            with patch.object(music.subprocess,'Popen',side_effect=create):
                player._player()
            self.assertEqual(len(seen),1)
            cmd,options=seen[0]
            self.assertIn('-STA',cmd)
            self.assertIn('PresentationCore',cmd[-1])
            self.assertIn('LouisF_shop.mp3',cmd[-1])
            self.assertEqual(options['stdout'],music.subprocess.DEVNULL)
            self.assertIn('creationflags',options)

    def test_windows_audio_failure_does_not_respawn_indefinitely(self):
        with patch.object(music.os,'name','nt'),patch.object(music.shutil,'which',return_value=r'C:\Windows\powershell.exe'):
            player=music.Music()
            fake_proc=Mock()
            fake_proc.poll.return_value=1
            fake_proc.wait.return_value=1
            fake_proc.returncode=1
            with patch.object(music.subprocess,'Popen',return_value=fake_proc) as popen:
                player._player()
            self.assertEqual(popen.call_count,1)
            self.assertFalse(player.enabled)
            self.assertFalse(player.available)

    def test_same_scenes_languages_and_engine_as_mac(self):
        self.assertEqual(len({p for p in music.TRACKS.values()}),5)
        self.assertTrue(all(p.exists() for p in music.TRACKS.values()))
        c=Controller()
        self.assertEqual(c.ui.language,'zh_CN')
        self.assertEqual(c.music_scene(),'title')

    def test_two_launchers_and_single_shared_play_script(self):
        root=Path(__file__).resolve().parents[1]
        self.assertIn('play.py',(root/'run.bat').read_text(encoding='utf-8-sig'))
        self.assertIn('play.py',(root/'run.command').read_text())
        self.assertTrue((root/'play.py').is_file())


if __name__=='__main__':unittest.main()
