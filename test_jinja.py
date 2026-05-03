import jinja2

env = jinja2.Environment(undefined=jinja2.StrictUndefined)
template = env.from_string("{{ app_actual.internal_network | default('SyntalixNet') }}")
try:
    print(template.render(app_actual={"nombre": "postgres"}))
except Exception as e:
    print("Error:", type(e), e)
