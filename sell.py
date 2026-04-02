"""
EchoWorks Daily Sales System
==============================
Run this every morning:

    python sell.py              Full interactive dashboard
    python sell.py snapshot     Pipeline only
    python sell.py actions      Today's actions only
    python sell.py message 34   Message for prospect #34
    python sell.py score        Weekly scorecard
    python sell.py objections   Objection playbook
"""

from aionos.sales.system import main

main()
