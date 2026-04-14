from dataclasses import dataclass

@dataclass
class SynthonState:
    n: int
    P: str          # polarity
    Phi: str        # criticality
    Omega: str      # topological protection
    O: str          # ouroboricity

def classify(n):
    if n == 1:
        return SynthonState(n, "P_sym", "Phi_c", "Omega_Z", "O2")
    elif n % 2 == 0:
        return SynthonState(n, "P_sym", "Phi_sub", "Omega_0", "O0")
    else:
        return SynthonState(n, "P_asym", "Phi_sub", "Omega_0", "O0")

def step(n):
    return n//2 if n % 2 == 0 else 3*n + 1

def collatz_synthon_trace(n0):
    n = n0
    trace = []

    while True:
        s = classify(n)
        trace.append(s)

        if n == 1:
            break

        n = step(n)

    return trace


if __name__ == "__main__":
    trace = collatz_synthon_trace(27)
    for t in trace:
        print(t)