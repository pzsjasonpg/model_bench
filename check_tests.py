import urllib.request, json
r = urllib.request.urlopen('http://localhost:8001/api/tests?page_size=3')
d = json.loads(r.read())

for t in d.get('items', []):
    print(f"\n=== Test ID={t['id']} status={t['status']} type={t['test_type']} ===")
    fp = t.get('fixed_params', '{}')
    print(f"fixed_params: {fp}")
    
    subtask_r = urllib.request.urlopen(f'http://localhost:8001/api/tests/{t["id"]}')
    sd = json.loads(subtask_r.read())
    for s in sd.get('subtasks', []):
        print(f"  SubTask#{s['seq']}: status={s['status']}")
        if s.get('command'):
            print(f"  CMD: {s['command']}")
        if s.get('result'):
            try:
                res = json.loads(s['result'])
                if res.get('_errors'):
                    print(f"  ERRORS: {res['_errors'][:5]}")
                else:
                    # Show key metrics
                    for k in ['qps','avg_latency_s','p50_latency_s','total_requests']:
                        if k in res:
                            print(f"  {k}: {res[k]}")
            except: pass
