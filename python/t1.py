import sys
  sys.path.insert(0, '/home/mrnob0dy666/SynthOmnicon')
  from agents.gatementat.tools import SynthoniconTool
  t = SynthoniconTool()

  print("=== meet ===")
  d, _ = t.run('meet', a='allosteric_domain', b='active_site')
  print(d)

  print("\n=== analogies ===")
  d, _ = t.run('analogies', name='allosteric_domain', limit=3)
  print(d)

  print("\n=== criticality ===")
  d, _ = t.run('criticality', name='allosteric_domain')
  print(d)