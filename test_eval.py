from jinja2 import Environment, StrictUndefined

env = Environment(undefined=StrictUndefined)

tests = [
    {"failed": True},
    {"failed": False},
    {"skipped": True},
    {"changed": True}
]

for t in tests:
    try:
        template = env.from_string("{{ not config_stack.failed | default(false) }}")
        res = template.render(config_stack=t)
        print(f"For {t}, result is: {res}")
    except Exception as e:
        print(f"For {t}, error: {e}")
