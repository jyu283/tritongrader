import subprocess

from tempfile import NamedTemporaryFile
from typing import TextIO

class Runner:
    DEFAULT_TIMEOUT_MS = 5000.0
    QEMU_ARM = "qemu-arm -L /usr/arm-linux-gnueabihf/ "

    def __init__(
        self,
        command: str,
        capture_output: bool = False,
        print_command: bool = False,
        print_output: bool = False,
        timeout_ms: float = DEFAULT_TIMEOUT_MS,
        text: bool = True,
        arm: bool = False,
    ):
        if arm:
            self.command = Runner.QEMU_ARM + self.command
        else:
            self.command = command
        
        self.capture_output = capture_output or print_output
        self.print_command = print_command
        self.print_output = print_output
        self.timeout_ms = timeout_ms
        self.text = text
        self.arm = arm
    
    def print_text_file(self, fp: TextIO, heading=""):
        if heading:
            print(heading)
        while True:
            line = fp.readline() 
            if not line:
                break
            print(line, end="")

    
    def run(self):
        if self.capture_output:
            self.outfp = NamedTemporaryFile("w+" if self.text else "w+b")
            self.errfp = NamedTemporaryFile("w+" if self.text else "w+b")
        
        if self.print_command:
            print(f"$ self.command")
        
        sp = subprocess.run(
            self.command,
            shell=True,
            stdout=self.outfp if self.capture_output else None,
            stderr=self.errfp if self.capture_output else None,
            text=self.text,
            arm=self.arm,
            timeout=self.timeout_ms / 1000,
        )

        if self.print_command:
            if not self.text:
                print("[binray output]")
            self.print_text_file(self.outfp, heading="=== STDOUT ===")
            self.print_text_file(self.errfp, heading="=== STDERR ===")
        
        self.outfp.close()
        self.errfp.close()
