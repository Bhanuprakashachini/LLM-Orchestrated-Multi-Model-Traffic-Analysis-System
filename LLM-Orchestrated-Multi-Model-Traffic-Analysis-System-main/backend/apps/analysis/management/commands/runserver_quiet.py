import sys
import os
from io import StringIO
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.management.base import BaseCommand


class Command(RunserverCommand):
    """
    Custom runserver command that suppresses development server warnings
    """
    
    def handle(self, *args, **options):
        # Override the inner_run method to suppress warnings
        original_inner_run = self.inner_run
        
        def quiet_inner_run(*args, **kwargs):
            # Capture stderr to filter warnings
            original_stderr = sys.stderr
            captured_stderr = StringIO()
            sys.stderr = captured_stderr
            
            try:
                result = original_inner_run(*args, **kwargs)
            finally:
                # Restore stderr and filter output
                sys.stderr = original_stderr
                stderr_content = captured_stderr.getvalue()
                
                # Filter out development server warnings
                lines = stderr_content.split('\n')
                filtered_lines = []
                skip_next = False
                
                for line in lines:
                    if "WARNING: This is a development server" in line:
                        skip_next = True
                        continue
                    elif skip_next and ("Do not use it in a production setting" in line or 
                                      "For more information on production servers" in line):
                        continue
                    else:
                        skip_next = False
                        if line.strip():  # Only add non-empty lines
                            filtered_lines.append(line)
                
                # Write filtered output
                if filtered_lines:
                    sys.stderr.write('\n'.join(filtered_lines) + '\n')
                
                return result
        
        self.inner_run = quiet_inner_run
        super().handle(*args, **options)