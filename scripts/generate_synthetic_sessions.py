"""
generate_synthetic_sessions.py
Generate synthetic labelled sessions for testing before real data is collected.

Usage:
    python scripts/generate_synthetic_sessions.py
"""
import os, json, random, uuid

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), '../data/sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)


def rand_mouse(n=200):
    events, x, y, t = [], 400, 300, 0.0
    for _ in range(n):
        t += random.uniform(15, 40)
        x += random.gauss(0, 5)
        y += random.gauss(0, 5)
        events.append({'type': 'mouse_move', 'ts': t, 'x': x, 'y': y})
    return events


def rand_keystrokes(label):
    events, t = [], random.uniform(1000, 3000)
    count = random.randint(10, 40)
    for _ in range(count):
        # Humans: natural rhythm with variance. Bots: fast and uniform.
        t += random.gauss(150, 30) if label == 'human' else random.uniform(5, 20)
        events.append({'type': 'keydown', 'ts': t, 'key': 'a', 'code': 'KeyA'})
        events.append({'type': 'keyup',   'ts': t + 80, 'key': 'a', 'code': 'KeyA'})
    return events


def rand_focuses(t_max):
    events = []
    for i in range(random.randint(2, 5)):
        t = random.uniform(500, t_max)
        events.append({'type': 'focus', 'ts': t, 'target': f'field_{i}'})
    return events


def rand_probes(label):
    delta_params = {
        'human':  (350, 80),    # moderate, natural variance
        'script': (20,  5),     # near-instant, very consistent
        'llm':    (800, 300),   # slow, high variance (inference overhead)
    }
    mu, sigma = delta_params[label]
    probes, t1 = [], 500.0
    for i in range(random.randint(4, 8)):
        t1    += random.uniform(3000, 7000)
        delta  = max(random.gauss(mu, sigma), 1.0)
        probes.append({
            'probeId': i + 1,
            't1':      t1,
            't2':      t1 + delta,
            'delta':   delta,
        })
    return probes


def make_session(label):
    session_id = str(uuid.uuid4())
    keystrokes = rand_keystrokes(label)
    t_max      = keystrokes[-1]['ts'] if keystrokes else 3000
    passive    = rand_mouse() + keystrokes + rand_focuses(t_max)
    probes     = rand_probes(label)

    return {
        'session_id':     session_id,
        'page_type':      random.choice(['login', 'checkout']),
        'label':          label,
        'start_time':     0,
        'end_time':       probes[-1]['t2'] + 2000 if probes else 5000,
        'passive_events': passive,
        'probes':         probes,
        'user_agent':     'Synthetic/1.0',
    }


def main():
    counts = {'human': 30, 'script': 5, 'llm': 5}
    total  = 0
    for label, n in counts.items():
        for _ in range(n):
            sess = make_session(label)
            path = os.path.join(SESSIONS_DIR,
                                f'{label}_{sess["session_id"][:8]}.json')
            with open(path, 'w') as f:
                json.dump(sess, f, indent=2)
            total += 1
    print(f'Generated {total} synthetic sessions → {SESSIONS_DIR}')
    print(f'  human: {counts["human"]}  script: {counts["script"]}  llm: {counts["llm"]}')


if __name__ == '__main__':
    main()