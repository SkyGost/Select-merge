"""
Konzolový test hernej logiky — overuje, či Board funguje správne
predtým, než pridáme UI.

Spustenie:  python test_logic.py
"""

import random
import sys

sys.path.insert(0, ".")

from game.board import Board


def test_initial_fill():
    print("=" * 60)
    print("TEST 1: Inicializácia poľa")
    print("=" * 60)
    board = Board()
    board._rng = random.Random(42)   # fixný seed pre opakovateľnosť
    board.fill_initial()
    print(board)
    print()

    # Skontrolovať, že každá bunka má kruh
    all_filled = all(
        board.grid[r][c] is not None
        for r in range(board.size) for c in range(board.size)
    )
    assert all_filled, "Niektoré bunky sú prázdne po fill_initial!"
    print("✓ Všetky bunky sú vyplnené")


def test_neighbors():
    print()
    print("=" * 60)
    print("TEST 2: Susedstvo")
    print("=" * 60)
    board = Board()

    # Roh (0,0) má 3 susedov
    n = board.get_neighbors(0, 0)
    print(f"Susedia (0,0): {n}")
    assert len(n) == 3, f"Roh by mal mať 3 susedov, mal {len(n)}"

    # Stred (2,2) má 8 susedov
    n = board.get_neighbors(2, 2)
    print(f"Susedia (2,2): {n}")
    assert len(n) == 8, f"Stred by mal mať 8 susedov, mal {len(n)}"

    # Hrana (0,2) má 5 susedov
    n = board.get_neighbors(0, 2)
    print(f"Susedia (0,2): {n}")
    assert len(n) == 5, f"Hrana by mala mať 5 susedov, mala {len(n)}"

    print("✓ Susedstvo funguje správne")


def test_adjacency():
    print()
    print("=" * 60)
    print("TEST 3: Kontrola susednosti dvoch buniek")
    print("=" * 60)
    assert Board.are_adjacent((0, 0), (0, 1)) is True   # orto
    assert Board.are_adjacent((0, 0), (1, 1)) is True   # diag
    assert Board.are_adjacent((0, 0), (2, 0)) is False  # ďaleko
    assert Board.are_adjacent((0, 0), (0, 0)) is False  # tá istá
    print("✓ Susednosť funguje správne")


def test_valid_path():
    print()
    print("=" * 60)
    print("TEST 4: Validácia spojnice")
    print("=" * 60)
    board = Board()
    # Ručne nastaviť pole pre kontrolovaný test
    from game.board import Circle
    # Nastav tri 4-ky v rade
    board.grid[0][0] = Circle(4, 0, 0)
    board.grid[0][1] = Circle(4, 0, 1)
    board.grid[0][2] = Circle(4, 0, 2)
    board.grid[1][0] = Circle(8, 1, 0)
    print(board)

    # Platná spojnica troch 4-iek
    path_ok = [(0, 0), (0, 1), (0, 2)]
    assert board.is_valid_path(path_ok), "Platná spojnica nebola uznaná!"
    print(f"✓ {path_ok} je platná")

    # Príliš krátka (len 1 kruh)
    assert not board.is_valid_path([(0, 0)])
    print("✓ Spojnica dĺžky 1 je neplatná")

    # Rôzne hodnoty
    bad_values = [(0, 0), (1, 0)]   # 4 a 8
    assert not board.is_valid_path(bad_values)
    print(f"✓ {bad_values} (rôzne hodnoty) je neplatná")

    # Nesusediace bunky
    bad_adj = [(0, 0), (0, 2)]
    assert not board.is_valid_path(bad_adj)
    print(f"✓ {bad_adj} (nesusedné) je neplatná")

    # Opakujúca sa bunka (pretínanie)
    bad_repeat = [(0, 0), (0, 1), (0, 0)]
    assert not board.is_valid_path(bad_repeat)
    print(f"✓ {bad_repeat} (opakovanie) je neplatná")


def test_merge():
    print()
    print("=" * 60)
    print("TEST 5: Vykonanie merge")
    print("=" * 60)
    board = Board()
    from game.board import Circle
    board.grid[0][0] = Circle(4, 0, 0)
    board.grid[0][1] = Circle(4, 0, 1)
    board.grid[0][2] = Circle(4, 0, 2)

    print("Pred merge:")
    print(board)

    path = [(0, 0), (0, 1), (0, 2)]
    score = board.merge_line(path)

    print(f"\nPo merge spojnice {path}, získané skóre: {score}")
    print(board)

    assert score == 8, f"Očakávané skóre 8, got {score}"
    assert board.grid[0][0] is None
    assert board.grid[0][1] is None
    assert board.grid[0][2].value == 8
    assert board.stats.score == 8
    assert board.stats.max_circle == 8
    print("✓ Merge funguje správne")


def test_gravity_and_spawn():
    print()
    print("=" * 60)
    print("TEST 6: Gravitácia + spawn nových kruhov")
    print("=" * 60)
    board = Board()
    board._rng = random.Random(123)
    board.fill_initial()

    # Urobíme dieru — vymažeme niektoré kruhy
    from game.board import Circle
    board.grid[0][2] = Circle(4, 0, 2)
    board.grid[1][2] = Circle(4, 1, 2)
    board.grid[2][2] = Circle(4, 2, 2)

    print("Pred merge:")
    print(board)

    path = [(0, 2), (1, 2), (2, 2)]
    board.merge_line(path)

    print("\nPo merge (mali by byť diery v stĺpci 2):")
    print(board)

    moves = board.apply_gravity()
    print(f"\nPo gravitácii ({len(moves)} pohybov):")
    print(board)

    new = board.spawn_new_circles()
    print(f"\nPo spawne {len(new)} nových kruhov:")
    print(board)


def test_game_over():
    print()
    print("=" * 60)
    print("TEST 7: Detekcia konca hry")
    print("=" * 60)
    board = Board()
    from game.board import Circle
    # Vytvor pole, kde žiadne dva susedy nemajú rovnakú hodnotu
    # Šachovnicový vzor 2 a 4
    for r in range(board.size):
        for c in range(board.size):
            board.grid[r][c] = Circle(2 if (r + c) % 2 == 0 else 4, r, c)

    # Ale susedia diagonálne majú rovnakú hodnotu! Toto NIE je game over.
    print("Šachovnicový vzor 2/4 (diagonálni susedia rovnakí):")
    print(board)
    assert not board.is_game_over(), "Diagonálni susedia rovnakí — nemal by byť koniec"
    print("✓ Diagonálni rovnakí susedia → nie je koniec hry")

    # Teraz urobme skutočný koniec — vzor kde ŽIADNI 8 susedia nemajú rovnakú hodnotu
    # Použijeme 4 rôzne hodnoty v rotačnom vzore 2x2
    values = [[2, 4, 2, 4, 2],
              [8, 16, 8, 16, 8],
              [2, 4, 2, 4, 2],
              [8, 16, 8, 16, 8],
              [2, 4, 2, 4, 2]]
    for r in range(board.size):
        for c in range(board.size):
            board.grid[r][c] = Circle(values[r][c], r, c)
    print("\nVzor kde diagonálni susedia sú rôzni:")
    print(board)
    # V tomto vzore (0,0)=2 a (1,1)=16, takže diagonála OK.
    # Ale (0,0)=2 a (0,2)=2 — to sú v rade 2 vzdialené, NIE susedia.
    # Skontrolujme, či sú dvojice rovnakých susedov...
    # (0,0)=2, susedia: (0,1)=4, (1,0)=8, (1,1)=16 — všetci rôzni. OK.
    assert board.is_game_over(), "Tento vzor by mal byť game over"
    print("✓ Detegovaný koniec hry")


if __name__ == "__main__":
    test_initial_fill()
    test_neighbors()
    test_adjacency()
    test_valid_path()
    test_merge()
    test_gravity_and_spawn()
    test_game_over()
    print()
    print("=" * 60)
    print("VŠETKY TESTY PREŠLI ✓")
    print("=" * 60)