import sys
msg = sys.stdin.read()
msg = msg.replace("qanoon-api", "legal-api")
msg = msg.replace("qanoon-rag", "rag-legal-search")
msg = msg.replace("qanoon", "legal-platform")
sys.stdout.write(msg)
