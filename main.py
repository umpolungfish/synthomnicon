"""
SynthOmnicon Main Entry Point

Provides two CLI entry points:
- synthomnicon: Full command name
- syncon: Short alias

Also exposes the agent framework for direct usage.
"""
from synthomnicon.cli import main, syncon_alias

# Export both CLI entry points
synthomnicon = main
syncon = syncon_alias

if __name__ == "__main__":
    # Default to main CLI
    main()
