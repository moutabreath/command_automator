cd C:\Windows\System32
set source=%1%
set destination=%2%
robocopy %source% %destination% /S /E /MT:16 /NFL /NDL /NJH /NJSs