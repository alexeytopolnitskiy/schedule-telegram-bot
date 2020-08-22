import pandas as pd

def give_text(data):

    head = False
    line = data.to_string(index=False, header=head)
    p = line.strip().split()
    k = 0
    while k < len(p):
        if p[k] == "-":
            p.insert(k-1, "\n")
            p.insert(k+3, "    ")
            k += 1
        k += 1
    p.insert(1, "              ")
    p = " ".join(p)
    p = p.replace("\n ", "\n")

    return p
