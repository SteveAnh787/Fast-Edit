set projectDir to "/Users/steveanh/Desktop/Quản lý project/Phần mềm bổ trợ YouTube/Render Fast YouTube/Render-Fast"
set shellCommand to "cd " & quoted form of projectDir & " && source .venv/bin/activate && python main.py >/tmp/render_fast_launcher.log 2>&1 &"

do shell script "bash -lc " & quoted form of shellCommand
