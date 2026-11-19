"""
Demo BFS & DFS pada graf "Studi Kasus" di slide (goal = U).
Mencetak trace  open = [...]; closed = [...]  persis seperti slide "Trace BFS" / "Trace of DFS".

    python demo_slide.py
"""
from algoritma.bfs import bfs
from algoritma.dfs import dfs

GRAF = dict(A="BCD", B="EF", C="GH", D="IJ", E="KL", F="LM", G="N", H="OP",
            I="PQ", J="R", K="S", L="T", P="U")


def succ(s):
    return list(enumerate(GRAF.get(s, "")))      # (operator, anak) urut kiri -> kanan


def goal(s):
    return s == "U"


def cetak(nama, fn, baris=11):
    r = fn("A", succ=succ, goal=goal)
    nama_state = r["by_label"]                   # label tampilan -> state asli
    print(f"=== {nama} ===")
    for k, t in enumerate(r["trace"][:baris], 1):
        op = ",".join(nama_state[x] for x in t["open"])
        cl = ",".join(nama_state[x] for x in t["closed"])
        print(f"{k:>2}. open = [{op}]; closed = [{cl}]")
    print(f"Jalur: {' -> '.join(r['states'])}  (d={r['d']}, dihasilkan={r['generated']}, "
          f"diperluas={r['expanded']}, Open maks={r['max_open']})\n")


if __name__ == "__main__":
    cetak("BFS (Open = Queue / FIFO)", bfs, 8)
    cetak("DFS (Open = Stack / LIFO)", dfs, 11)
