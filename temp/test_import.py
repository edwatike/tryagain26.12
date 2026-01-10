import sys
sys.path.insert(0, 'D:\\tryagain\\backend')

from app.usecases import start_parsing
print(f"Type of start_parsing: {type(start_parsing)}")
print(f"Has execute method: {hasattr(start_parsing, 'execute')}")
if hasattr(start_parsing, 'execute'):
    print(f"Execute method: {start_parsing.execute}")
else:
    print(f"Dir: {dir(start_parsing)}")








