import cProfile
import random
import tkinter as tk
from tkinter import font
from collections import deque
from tqdm import tqdm
import pstats
from io import StringIO

class NurikabeSolver:
    def __init__(self, puzzle, update_gui_callback=None):
        # Inicializácia solvera, nastavuje veľkosť mriežky, vstupný puzzle, a prípadný callback na aktualizáciu GUI.
        self.n = 5
        self.puzzle = puzzle
        self.update_gui_callback = update_gui_callback
        
        self.island_numbers = [[0] * self.n for _ in range(self.n)]
        for r in range(self.n):
            for c in range(self.n):
                if self.puzzle[r][c] > 0:
                    self.island_numbers[r][c] = self.puzzle[r][c]

        self.solution = [[None] * self.n for _ in range(self.n)]
        # PÔVODNÝ KÓD, KTORÝ BOL ODSTRÁNENÝ:
        for r in range(self.n):
            for c in range(self.n):
                if self.island_numbers[r][c] > 0:
                     self.solution[r][c] = "W"

        self.state_count = 0

    def solve_with_dfs(self):
        # Rieši puzzle pomocou hĺbkového prehľadávania (DFS).
        self.state_count = 0
        return self._dfs(0, 0)

    def _dfs(self, r, c):
        # Rekurzívna funkcia na implementáciu DFS, kontroluje správnosť parciálneho riešenia.
        if r == self.n:
            return self.check_final_solution()

        next_r, next_c = (r, c + 1) if c + 1 < self.n else (r + 1, 0)

        if self.solution[r][c] is not None:
            return self._dfs(next_r, next_c)

        # Namiesto pevného ["W", "B"] použijeme LCV, aby sme poradie farieb vyberali inteligentnejšie
        colors = self.order_values_by_LCV(r, c)

        for color in colors:
            self.solution[r][c] = color
            self.state_count += 1

            if self.update_gui_callback:
                self.update_gui_callback(self.solution)

            if self.partial_check():
                if self._dfs(next_r, next_c):
                    return True

            self.solution[r][c] = None

        return False

    def solve_with_backtracking(self):
        # Rieši puzzle pomocou spätného sledovania (Backtracking).
        self.state_count = 0
        return self._backtrack()

    def _backtrack(self):
        # Rekurzívna funkcia na implementáciu spätného sledovania s použitím MRV a LCV heuristiky.
        r, c = self.find_unassigned_MRV_degree()
        if r == -1 and c == -1:
            return self.check_final_solution()

        # Farby usporiadame podľa LCV heuristiky
        colors = self.order_values_by_LCV(r, c)

        for color in colors:
            self.solution[r][c] = color
            self.state_count += 1

            if self.update_gui_callback:
                self.update_gui_callback(self.solution)

            if self.partial_check():
                if self._backtrack():
                    return True

            self.solution[r][c] = None

        return False

    def find_unassigned_MRV_degree(self):
        # Nájde políčko na základe MRV (minimum remaining values) a degree heuristiky.
        # MRV: hľadáme políčko s najmenšou doménou (najmenej povolených farieb)
        # ak je remíza, použijeme degree heuristic
        unassigned = [(r, c) for r in range(self.n) for c in range(self.n) if self.solution[r][c] is None]
        if not unassigned:
            return -1, -1

        best_cell = None
        best_domain_size = float('inf')
        best_degree = -1

        for (r, c) in unassigned:
            domain_size = self.domain_size(r, c)
            if domain_size < best_domain_size:
                # Nové lepšie políčko z hľadiska MRV
                best_domain_size = domain_size
                best_cell = (r, c)
                # degree heuristika sa znovu hodnotí
                best_degree = self.unassigned_neighbors_count(r, c)
            elif domain_size == best_domain_size:
                # Remíza, použijeme degree heuristic
                deg = self.unassigned_neighbors_count(r, c)
                if deg > best_degree:
                    best_degree = deg
                    best_cell = (r, c)

        return best_cell if best_cell is not None else (-1, -1)

    def domain_size(self, r, c):
        # Vypočíta veľkosť domény pre konkrétne políčko (počet platných hodnôt).
        # Zistí, koľko farieb môže byť priradených do (r,c), aby partial_check nepadol
        # Otestujeme "W" a "B"
        count = 0
        for color in ["W", "B"]:
            self.solution[r][c] = color
            if self.partial_check():
                count += 1
            self.solution[r][c] = None
        return count

    def unassigned_neighbors_count(self, r, c):
        # Počíta počet nevyplnených susedov pre dané políčko.
        # Degree heuristic: koľko nevyplnených susedov má toto políčko?
        neighbors = [(r+1,c),(r-1,c),(r,c+1),(r,c-1)]
        count = 0
        for nr, nc in neighbors:
            if 0 <= nr < self.n and 0 <= nc < self.n:
                if self.solution[nr][nc] is None:
                    count += 1
        return count

    def order_values_by_LCV(self, r, c):
        # Usporiadava farby podľa LCV (least constraining value) heuristiky.
        # LCV: Vyberieme poradie farieb podľa toho, ktorá menej obmedzí ostatné nevyplnené políčka
        # V jednoduchosti: po priradení farby pozrieme na domain_size ostatných políčok a zistíme priemerné zníženie
        # Pre zjednodušenie tu iba spočítame, koľkým políčkam sa pri priradení danej farby zhorší domain_size.

        def constraining_measure(color):
            # priradíme farbu a zmeriame vplyv
            self.solution[r][c] = color
            if not self.partial_check():
                # Táto farba hneď padá, je maximálne obmedzujúca
                measure = float('inf')
            else:
                measure = 0
                # Spočítame počet políčok, ktorým by mohlo klesnúť domain_size
                # Teraz bez modifikácie stavu, len heuristicky zistíme domain pre ostatné
                unassigned = [(rr, cc) for rr in range(self.n) for cc in range(self.n) if self.solution[rr][cc] is None and (rr, cc) != (r, c)]
                for (rr, cc) in unassigned:
                    dsize = self.domain_size(rr, cc)
                    if dsize == 0:
                        # Ak farba spôsobí, že nejaké iné políčko nemá žiadnu možnosť, je to veľmi obmedzujúce
                        measure += 10
                    elif dsize == 1:
                        # Mierne obmedzujúce
                        measure += 1
            self.solution[r][c] = None
            return measure

        color_candidates = ["W","B"]
        # Vyhodnotíme, ktorá farba je menej obmedzujúca
        # Nižšie skóre = menej obmedzení pre ostatné
        scores = [(color, constraining_measure(color)) for color in color_candidates]
        scores.sort(key=lambda x: x[1])
        # Vrátime farby v poradí od najmenej obmedzujúcej po najviac obmedzujúcu
        return [s[0] for s in scores]

    def solve_with_forward_checking(self):
        # Rieši puzzle pomocou forward-checkingu.
        self.state_count = 0
        return self._forward_checking()

    def _forward_checking(self):
        # Rekurzívna implementácia forward-checkingu s kontrolou obmedzení.
        r, c = self.find_unassigned()
        if r == -1 and c == -1:
            return self.check_final_solution()

        for color in ["W", "B"]:
            self.solution[r][c] = color
            self.state_count += 1

            if self.update_gui_callback:
                self.update_gui_callback(self.solution)

            if self.forward_check(r, c, color):
                if self._forward_checking():
                    return True

            self.solution[r][c] = None

        return False

    def find_unassigned(self):
        # Nájde prvé nevyplnené políčko.
        for rr in range(self.n):
            for cc in range(self.n):
                if self.solution[rr][cc] is None:
                    return rr, cc
        return -1, -1

    def forward_check(self, r, c, color):
        # Overuje platnosť riešenia pri forward-checkingu.
        return self.check_all_white_components_FC() and not self.forms_black_loop(r, c) and self.check_islands_separate()

    def partial_check(self):
        # Čiastočná validácia aktuálneho riešenia.
        for r in range(self.n):
            for c in range(self.n):
                if self.island_numbers[r][c] > 0 and self.solution[r][c] == "B":
                    return False

        visited = set()
        for r in range(self.n):
            for c in range(self.n):
                if self.solution[r][c] == "W" and (r, c) not in visited:
                    whites, numbers = self.get_white_component(r, c, visited)
                    if len(numbers) == 1:
                        nr, nc = numbers[0]
                        required = self.island_numbers[nr][nc]
                        if len(whites) > required:
                            return False

        black_cells = [(rr, cc) for rr in range(self.n) for cc in range(self.n) if self.solution[rr][cc] == "B"]
        if self.forms_black_loop_partial(black_cells):
            return False

        return True

    def forms_black_loop_partial(self, black_cells):
        # Overuje, či čierne bunky tvoria cyklus počas čiastočného riešenia.
        if len(black_cells) < 4:
            return False

        adj = {cell: [] for cell in black_cells}
        for (rr, cc) in black_cells:
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = rr + dr, cc + dc
                if (nr, nc) in adj:
                    adj[(rr, cc)].append((nr, nc))

        visited = set()

        def dfs_cycle(u, parent, depth):
            visited.add(u)
            for v in adj[u]:
                if v not in visited:
                    if dfs_cycle(v, u, depth + 1):
                        return True
                elif v != parent and depth >= 3:
                    return True
            return False

        visited_global = set()
        for cell in black_cells:
            if cell not in visited_global:
                visited.clear()
                if dfs_cycle(cell, None, 0):
                    return True
                visited_global.update(visited)

        return False

    def get_white_component(self, r, c, visited):
        #Nájde komponent bielych buniek, ktoré súvisia s daným políčkom.
        stack = [(r, c)]
        whites = []
        numbers = []
        while stack:
            rr, cc = stack.pop()
            if (rr, cc) in visited:
                continue
            visited.add((rr, cc))
            if self.solution[rr][cc] == "W":
                whites.append((rr, cc))
                if self.island_numbers[rr][cc] > 0:
                    numbers.append((rr, cc))
                for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < self.n and 0 <= nc < self.n:
                        if self.solution[nr][nc] == "W":
                            stack.append((nr, nc))
        return whites, numbers

    def check_final_solution(self):
        # Overuje, či je riešenie finálne a splňuje všetky podmienky.
        return (
            self.check_all_white_components() and
            self.check_islands_separate() and
            self.check_island_sizes() and
            self.check_black_contiguous() and
            not self.forms_black_loop_final()
        )

    def check_all_white_components(self):
        # Overuje, či všetky biele komponenty splňujú pravidlá.
        visited = set()
        for r in range(self.n):
            for c in range(self.n):
                if self.solution[r][c] == "W" and (r, c) not in visited:
                    comp_whites, comp_numbers = self.get_white_component(r, c, visited)
                    if len(comp_numbers) > 1:
                        return False
                    elif len(comp_numbers) == 1:
                        nr, nc = comp_numbers[0]
                        required = self.island_numbers[nr][nc]
                        if len(comp_whites) != required:
                            return False
                    else:
                        if not self.can_reach_any_island(comp_whites):
                            return False
        return True

    def check_all_white_components_FC(self):
        # Verzia pre forward-checking, kontroluje biele komponenty.
        visited = set()
        for r in range(self.n):
            for c in range(self.n):
                if self.solution[r][c] == "W" and (r, c) not in visited:
                    comp_whites, comp_numbers = self.get_white_component(r, c, visited)
                    if len(comp_numbers) > 1:
                        return False
                    elif len(comp_numbers) == 1:
                        nr, nc = comp_numbers[0]
                        required = self.island_numbers[nr][nc]
                        if len(comp_whites) > required:
                            return False
                    else:
                        reachable = self.can_reach_any_island(comp_whites)
                        if not reachable:
                            return False
        return True

    def can_reach_any_island(self, comp_whites):
        # Kontroluje, či biele políčko má prístup k číslu (z mapy)
        islands = [(r, c) for r in range(self.n) for c in range(self.n) if self.island_numbers[r][c] > 0]
        if not islands:
            return True

        visited = set(comp_whites)
        frontier = deque(comp_whites)
        while frontier:
            rr, cc = frontier.popleft()
            if self.island_numbers[rr][cc] > 0:
                return True
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < self.n and 0 <= nc < self.n:
                    if (nr, nc) not in visited:
                        if self.solution[nr][nc] in [None, "W"]:
                            visited.add((nr, nc))
                            frontier.append((nr, nc))
        return False

    def forms_black_loop(self, r, c):
        # Overuje, či čierne bunky tvoria cyklus.
        black_cells = [(rr, cc) for rr in range(self.n) for cc in range(self.n) if self.solution[rr][cc] == "B"]
        if len(black_cells) < 4:
            return False

        adj = {cell: [] for cell in black_cells}
        for (rr, cc) in black_cells:
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = rr + dr, cc + dc
                if (nr, nc) in adj:
                    adj[(rr, cc)].append((nr, nc))

        visited = set()

        def dfs_cycle(u, parent, depth):
            visited.add(u)
            for v in adj[u]:
                if v not in visited:
                    if dfs_cycle(v, u, depth + 1):
                        return True
                elif v != parent and depth >= 3:
                    return True
            return False

        visited_global = set()
        for cell in black_cells:
            if cell not in visited_global:
                visited.clear()
                if dfs_cycle(cell, None, 0):
                    return True
                visited_global.update(visited)

        return False

    def check_islands_separate(self):
        # Overuje, či sú všetky ostrovy oddelené.
        island_positions = [(r, c) for r in range(self.n) for c in range(self.n) if self.island_numbers[r][c] > 0]

        def get_island_component(rr, cc):
            visited = set()
            q = deque()
            q.append((rr, cc))
            visited.add((rr, cc))
            while q:
                r_, c_ = q.popleft()
                for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = r_ + dr, c_ + dc
                    if 0 <= nr < self.n and 0 <= nc < self.n:
                        if self.solution[nr][nc] == "W" and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            q.append((nr, nc))
            return visited

        island_components = []
        seen_islands = set()
        for (ir, ic) in island_positions:
            val = self.island_numbers[ir][ic]
            if val in seen_islands:
                continue
            seen_islands.add(val)
            comp = get_island_component(ir, ic)
            island_components.append((val, comp))

        for i in range(len(island_components)):
            for j in range(i + 1, len(island_components)):
                _, comp1 = island_components[i]
                _, comp2 = island_components[j]
                if self.island_touch(comp1, comp2):
                    return False
        return True

    def island_touch(self, comp1, comp2):
        # Overuje, či sa dva ostrovy dotýkajú.
        for (r, c) in comp1:
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in comp2:
                    return True
        return False

    def check_island_sizes(self):
        # Overuje, či majú všetky ostrovy správne veľkosti.
        island_positions = [(r, c) for r in range(self.n) for c in range(self.n) if self.island_numbers[r][c] > 0]
        processed = set()
        for (ir, ic) in island_positions:
            val = self.island_numbers[ir][ic]
            if val in processed:
                continue
            processed.add(val)
            if not self.check_single_island_size(ir, ic, val):
                return False
        return True

    def check_single_island_size(self, ir, ic, val):
        # Overuje veľkosť jedného ostrova.
        if self.solution[ir][ic] != "W":
            return False
        visited = set([(ir, ic)])
        q = deque([(ir, ic)])
        while q:
            r_, c_ = q.popleft()
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r_ + dr, c_ + dc
                if 0 <= nr < self.n and 0 <= nc < self.n:
                    if self.solution[nr][nc] == "W" and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
        required_size = self.island_numbers[ir][ic]
        return len(visited) == required_size

    def check_black_contiguous(self):
        # Kontroluje, či sú všetky čierne bunky súvislé.
        blacks = [(r, c) for r in range(self.n) for c in range(self.n) if self.solution[r][c] == "B"]
        if not blacks:
            return True
        visited = set([blacks[0]])
        q = deque([blacks[0]])
        while q:
            r_, c_ = q.popleft()
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r_ + dr, c_ + dc
                if (nr, nc) in blacks and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return len(visited) == len(blacks)

    def forms_black_loop_final(self):
        # Overuje, či čierne bunky tvoria cyklus vo finálnom riešení.
        black_cells = [(rr, cc) for rr in range(self.n) for cc in range(self.n) if self.solution[rr][cc] == "B"]
        if len(black_cells) < 4:
            return False

        adj = {cell: [] for cell in black_cells}
        for (rr, cc) in black_cells:
            for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = rr + dr, cc + dc
                if (nr, nc) in adj:
                    adj[(rr, cc)].append((nr, nc))

        visited = set()

        def dfs_cycle(u, parent, depth):
            visited.add(u)
            for v in adj[u]:
                if v not in visited:
                    if dfs_cycle(v, u, depth + 1):
                        return True
                elif v != parent and depth >= 3:
                    return True
            return False

        visited_global = set()
        for cell in black_cells:
            if cell not in visited_global:
                visited.clear()
                if dfs_cycle(cell, None, 0):
                    return True
                visited_global.update(visited)

        return False


puzzles = [
    [
        [0,0,2,0,0],
        [0,1,0,0,0],
        [0,0,0,3,0],
        [0,0,0,0,0],
        [4,0,0,0,0]
    ],
    [
        [0,0,0,0,0],
        [0,1,0,0,3],
        [0,0,0,0,0],
        [6,0,0,1,0],
        [0,0,0,0,0]
    ],
    [
        [0,4,0,5,0],
        [0,0,0,0,0],
        [0,0,1,0,0],
        [4,0,0,0,0],
        [0,0,0,0,0]
    ],
    [
        [0,0,1,0,0],
        [0,2,0,0,0],
        [0,0,0,3,0],
        [0,0,0,0,0],
        [4,0,0,0,0]
    ],
    [
        [1,0,0,0,0],
        [0,0,0,2,0],
        [0,0,0,0,0],
        [0,3,0,0,0],
        [0,0,0,0,4]
    ],
    [
        [0,0,3,0,0],
        [0,3,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [2,0,0,0,4]
    ],
    [
        [0,0,0,2,0],
        [0,1,0,0,0],
        [0,0,0,0,3],
        [0,0,0,0,0],
        [4,0,0,0,0]
    ],
    #nevyriesitelny
    [
        [0,1,0,0,0],
        [0,0,0,2,0],
        [0,0,0,0,0],
        [0,0,3,0,0],
        [4,0,0,0,0]
    ],
    #nevyriesitelny
    [
        [0,2,0,0,0],
        [1,0,0,0,0],
        [0,0,0,0,3],
        [0,0,0,0,0],
        [4,0,0,0,0]
    ],
    #nevyriesitelny
    [
        [2,0,0,0,0],
        [0,0,0,0,3],
        [0,0,1,0,0],
        [0,0,0,0,0],
        [4,0,0,0,0]
    ]
]

class NurikabeGUI:
    def __init__(self, master):
        # Inicializácia GUI aplikácie, vytvára hlavné okno, tlačidlá a mriežku.
        self.master = master
        self.master.title("Nurikabe Solver")

        self.current_puzzle_index = 0
        self.visualize = tk.BooleanVar(value=True)  # Stav prepínača vizualizácie

        main_frame = tk.Frame(self.master, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.Y)

        grid_frame = tk.Frame(main_frame, bg="#dcdcdc", bd=2, relief="sunken")
        grid_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Zvýšené písmo pre tlačidlá, nadpisy a popis iterácií
        title_font = font.Font(size=16, weight="bold")
        button_font = font.Font(size=14, weight="bold")
        label_font = font.Font(size=16, weight="bold")

        # Nadpis zobrazujúci aktuálny level
        self.level_label = tk.Label(button_frame, text="Level: 1", font=title_font, fg="#007ACC", bg="#f0f0f0")
        self.level_label.pack(pady=10)

        # Tlačidlá so zväčšenými rozmermi
        self.next_level_button = tk.Button(button_frame, text="Ďalší Level", command=self.next_level, font=button_font, height=2, width=20, bg="#007ACC", fg="white", relief="raised", bd=2)
        self.next_level_button.pack(pady=10)

        self.dfs_button = tk.Button(button_frame, text="DFS", command=self.profile_dfs, font=button_font, height=2, width=20, bg="#4CAF50", fg="white", relief="raised", bd=2)
        self.dfs_button.pack(pady=10)

        self.backtracking_button = tk.Button(button_frame, text="Backtracking", command=self.profile_backtracking, font=button_font, height=2, width=20, bg="#FF9800", fg="white", relief="raised", bd=2)
        self.backtracking_button.pack(pady=10)

        self.forward_button = tk.Button(button_frame, text="Forward Checking", command=self.profile_forward_checking, font=button_font, height=2, width=20, bg="#F44336", fg="white", relief="raised", bd=2)
        self.forward_button.pack(pady=10)

        # Prepínač pre vizualizáciu
        self.visualize_switch = tk.Checkbutton(button_frame, text="Zobraziť iterácie", variable=self.visualize, font=label_font, bg="#f0f0f0", fg="#333333", selectcolor="#D3D3D3")
        self.visualize_switch.pack(pady=20)

        # Popis iterácií s väčším písmom
        self.iteration_label = tk.Label(button_frame, text="Počet iterácií: 0", font=label_font, fg="#333333", bg="#f0f0f0")
        self.iteration_label.pack(pady=20)

        # Mriežka pre zobrazenie puzzlu
        self.cells = []
        self.number_font = font.Font(size=14, weight="bold")  # Menšie písmo pre moderný vzhľad

        for r in range(5):
            row_cells = []
            for c in range(5):
                cell = tk.Label(grid_frame, text="", relief="ridge", borderwidth=2, bg="white", fg="black", font=self.number_font, width=4, height=2)
                cell.grid(row=r, column=c, sticky='nsew', padx=2, pady=2)
                row_cells.append(cell)
            self.cells.append(row_cells)

        for r in range(5):
            grid_frame.rowconfigure(r, weight=1)
        for c in range(5):
            grid_frame.columnconfigure(c, weight=1)

        self.load_puzzle()

    def load_puzzle(self):
        # Načíta aktuálny puzzle do mriežky.
        self.level_label.config(text=f"Level: {self.current_puzzle_index + 1}")

        puzzle = puzzles[self.current_puzzle_index]
        for r in range(5):
            for c in range(5):
                self.cells[r][c].config(text="", bg="white", fg="black")
        for r in range(5):
            for c in range(5):
                val = puzzle[r][c]
                if val > 0:
                    self.cells[r][c].config(text=str(val), fg="#007ACC", bg="white")
                else:
                    self.cells[r][c].config(text="", fg="black", bg="white")

        self.master.title(f"Nurikabe Solver - Level {self.current_puzzle_index + 1}")

    def next_level(self):
        # Presunie sa na ďalší level a resetuje iterácie.
        self.current_puzzle_index = (self.current_puzzle_index + 1) % len(puzzles)
        self.iteration_label.config(text="Počet iterácií: 0")  # Resetujeme počet iterácií
        self.load_puzzle()

    def profile_dfs(self):
        # Profiluje riešenie pomocou DFS.
        self.profile_algorithm(self.run_dfs)

    def profile_backtracking(self):
        # Profiluje riešenie pomocou Backtrackingu.
        self.profile_algorithm(self.run_backtracking)

    def profile_forward_checking(self):
        # Profiluje riešenie pomocou Forward-Checkingu.
        self.profile_algorithm(self.run_forward_checking)

    def reset_iterations(self):
        # Resetuje počítadlo iterácií.
        self.iteration_label.config(text="Počet iterácií: 0")

    def profile_algorithm(self, algorithm):
        # Profiluje zadaný algoritmus a vypíše štatistiky.
        profiler = cProfile.Profile()
        profiler.enable()
        algorithm()
        profiler.disable()

        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats(pstats.SortKey.CALLS)
        ps.print_stats()

        print("Profilovanie výsledky:")
        print(s.getvalue())

    def run_dfs(self):
        # Spustí riešenie aktuálneho levelu pomocou DFS.
        puzzle = puzzles[self.current_puzzle_index]
        solver = NurikabeSolver(puzzle, update_gui_callback=self.safe_update_gameboard if self.visualize.get() else None)
        solved = solver.solve_with_dfs()
        self.show_solution(solver, solved)

    def run_backtracking(self):
        # Spustí riešenie aktuálneho levelu pomocou Backtrackingu.
        puzzle = puzzles[self.current_puzzle_index]
        solver = NurikabeSolver(puzzle, update_gui_callback=self.safe_update_gameboard if self.visualize.get() else None)
        solved = solver.solve_with_backtracking()
        self.show_solution(solver, solved)

    def run_forward_checking(self):
        # Spustí riešenie aktuálneho levelu pomocou Forward-Checkingu.
        puzzle = puzzles[self.current_puzzle_index]
        solver = NurikabeSolver(puzzle, update_gui_callback=self.safe_update_gameboard if self.visualize.get() else None)
        solved = solver.solve_with_forward_checking()
        self.show_solution(solver, solved)

    def safe_update_gameboard(self, solution):
        # Bezpečne aktualizuje hracie pole počas vizualizácie.
        self.update_gameboard(solution)
        self.master.update_idletasks()  # Aktualizuje GUI na zobrazenie aktuálneho stavu.

    def update_gameboard(self, solution):
        # Aktualizuje mriežku na základe aktuálneho riešenia.
        puzzle = puzzles[self.current_puzzle_index]
        for r in range(5):
            for c in range(5):
                val = puzzle[r][c]
                if val > 0:
                    self.cells[r][c].config(text=str(val), fg="#007ACC", bg="white")
                else:
                    color = solution[r][c]
                    if color == 'W':
                        self.cells[r][c].config(bg="white")
                    elif color == 'B':
                        self.cells[r][c].config(bg="black")
                    else:
                        self.cells[r][c].config(bg="white")

    def show_solution(self, solver, solved):
        # Zobrazuje finálne riešenie alebo stav pri neúspechu.
        if not solved:
            self.iteration_label.config(text=f"Počet iterácií: {solver.state_count}")
            self.master.title(f"Nurikabe Solver - Nepodarilo sa vyriešiť (Level {self.current_puzzle_index + 1})")
            return

        self.iteration_label.config(text=f"Počet iterácií: {solver.state_count}")
        self.master.title(f"Nurikabe Solver - Riešenie nájdené (Level {self.current_puzzle_index + 1})")

        for r in range(5):
            for c in range(5):
                val = puzzles[self.current_puzzle_index][r][c]
                color = solver.solution[r][c]
                if val > 0:
                    self.cells[r][c].config(text=str(val), fg="#007ACC", bg="white")
                else:
                    if color == 'W':
                        self.cells[r][c].config(bg="white")
                    else:
                        self.cells[r][c].config(bg="black")

if __name__ == "__main__":
    root = tk.Tk()

    # Nastavenie maximalizovaného okna
    root.state('zoomed')

    app = NurikabeGUI(root)
    root.mainloop()
