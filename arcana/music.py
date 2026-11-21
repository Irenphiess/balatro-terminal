"""User-supplied tracks: macOS afplay or Windows PowerShell MediaPlayer."""
from __future__ import annotations
import os,sys,shutil,subprocess,threading,pathlib

ASSETS=pathlib.Path(__file__).resolve().parent.parent/'assets'
TRACKS={
    'title':ASSETS/'LouisF_main.mp3',
    'play':ASSETS/'LouisF_main.mp3',
    'shop':ASSETS/'LouisF_shop.mp3',
    'boss':ASSETS/'LouisF_boss.mp3',
    'arcana':ASSETS/'LouisF_arcana.mp3',
    'celestial':ASSETS/'LouisF_celestial.mp3',
    'pack':ASSETS/'LouisF_main.mp3',
}  # Main also covers ordinary battle, Standard packs and Buffoon packs.


class Music:
    def __init__(self,enabled=True):
        self.available=((sys.platform=='darwin' and shutil.which('afplay') is not None) or (os.name=='nt' and (shutil.which('powershell.exe') or shutil.which('powershell')) is not None)) and all(p.is_file() for p in TRACKS.values())
        self.enabled=bool(enabled and self.available)
        self.scene='title'
        self._stop=threading.Event();self._thread=None;self._proc=None
    def set_scene(self,scene):
        if scene not in TRACKS:scene='play'
        if self.scene==scene:return
        self.scene=scene
        # Interrupt only the old melody. The worker immediately starts the new scene.
        proc=self._proc
        if proc and proc.poll() is None:
            try:proc.terminate()
            except OSError:pass
    def _player(self):
        while self.enabled and not self._stop.is_set():
            active=self.scene
            try:
                if os.name=='nt':
                    # Windows PresentationCore is installed with Windows PowerShell/.NET.
                    # Each scene runs in its own process; terminating it changes tracks.
                    path=str(TRACKS[active]).replace("'","''")
                    script=("Add-Type -AssemblyName PresentationCore; "
                            "$p=New-Object System.Windows.Media.MediaPlayer; "
                            "$p.Open([Uri]::new('"+path+"')); "
                            "$p.Volume=0.23; $p.Play(); "
                            "while($true){Start-Sleep -Milliseconds 200; "
                            "if($p.NaturalDuration.HasTimeSpan -and "
                            "$p.Position -ge $p.NaturalDuration.TimeSpan){$p.Position=[TimeSpan]::Zero;$p.Play()}}")
                    shell=shutil.which('powershell.exe') or shutil.which('powershell')
                    proc=subprocess.Popen([shell,'-NoProfile','-NonInteractive','-STA','-Command',script],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                else:
                    proc=subprocess.Popen(['afplay','-v','0.23',str(TRACKS[active])],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                self._proc=proc
                while proc.poll() is None:
                    if self._stop.wait(.08) or not self.enabled or self.scene!=active:
                        try:proc.terminate()
                        except OSError:pass
                        break
                try:proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=1)
                # A missing codec/PresentationCore can make PowerShell exit
                # immediately. Don't spawn failing players in a tight loop.
                if (os.name=='nt' and proc.returncode not in (None,0)
                    and self.scene==active and not self._stop.is_set()):
                    self.available=False
                    self.enabled=False
            except (OSError,subprocess.TimeoutExpired):
                self.enabled=False
            finally:self._proc=None
    def start(self):
        if self.enabled and not (self._thread and self._thread.is_alive()):
            self._stop.clear()
            self._thread=threading.Thread(target=self._player,name='BalatroSceneAudio',daemon=True)
            self._thread.start()
    def stop(self):
        self._stop.set()
        proc=self._proc
        if proc and proc.poll() is None:
            try:proc.terminate()
            except OSError:pass
        if self._thread and self._thread.is_alive():self._thread.join(timeout=2)
        self._thread=None
    def toggle(self):
        if not self.available:return False
        if self.enabled:self.enabled=False;self.stop()
        else:self.enabled=True;self.start()
        return self.enabled

def resize_terminal(cols=160,rows=60):
    """Request a larger terminal viewport; some terminals ignore this escape."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):return False
    cols=max(80,min(240,int(cols)));rows=max(24,min(90,int(rows)))
    sys.stdout.write(f'\033[8;{rows};{cols}t');sys.stdout.flush()
    return True
