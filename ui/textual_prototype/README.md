UI Textual Prototype (Phase 2)

This directory contains a minimal Textual-based user interface to prototype deployment management in Phase 2. It currently:
- Lists deployments derived from a mock DependencyGraph
- Shows details for the selected deployment
- Can generate a simple deployment plan via the g key

Usage:
- Run: python ui/textual_prototype/app.py
- Navigate: n / j / down to move forward; p / k / up to move backward
- Generate plan: press g

Note: This is a scaffold. The DependencyGraph is mocked and will be replaced with a real integration in later phases.
