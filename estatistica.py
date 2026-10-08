import csv
import math
import re


def _number(token):
    try:
        value = float(token)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"valor não numérico: {token!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"valor deve ser finito: {token!r}")
    return value


def parse_values(text):
    """Lê números separados por vírgula, ponto e vírgula ou espaço."""
    tokens = [part for part in re.split(r"[,;\s]+", text.strip()) if part]
    if not tokens:
        raise ValueError("informe ao menos um número")
    return [_number(token) for token in tokens]


def load_csv(path):
    """Lê um CSV numérico; aceita cabeçalho textual na primeira linha."""
    values = []
    first_data_row = True
    with open(path, encoding="utf-8-sig", newline="") as file:
        sample = file.read(2048)
        file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        for row in csv.reader(file, dialect):
            cells = [cell.strip() for cell in row if cell.strip()]
            if not cells:
                continue
            parsed = []
            invalid = None
            for cell in cells:
                try:
                    parsed.append(_number(cell))
                except ValueError as error:
                    invalid = error
                    break
            if invalid:
                if first_data_row and not parsed and not values:
                    # Permite cabeçalho somente se a linha inteira for textual.
                    if all(_is_text(cell) for cell in cells):
                        first_data_row = False
                        continue
                raise ValueError(f"texto inesperado no CSV: {invalid}") from invalid
            values.extend(parsed)
            first_data_row = False
    if not values:
        raise ValueError("o CSV não contém valores numéricos")
    return values


def _is_text(token):
    try:
        _number(token)
        return False
    except ValueError:
        return True


def ungrouped_summary(values):
    """Parte 1: usa diretamente as funções exigidas do módulo statistics."""
    import statistics

    return {
        "mode": statistics.mode(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
    }


def discrete_summary(values):
    """Parte 2: calcula as medidas exclusivamente a partir da tabela de fi/Fi."""
    from collections import Counter

    counts = Counter(values)
    rows = []
    cumulative = 0
    for value, frequency in sorted(counts.items()):
        cumulative += frequency
        rows.append((value, frequency, cumulative))

    n = cumulative
    max_frequency = max(row[1] for row in rows)
    modes = [value for value, frequency, _ in rows if frequency == max_frequency]
    weighted_sum = sum(value * frequency for value, frequency, _ in rows)

    def value_at(rank):
        return next(value for value, _, fi_cumulative in rows if fi_cumulative >= rank)

    if n % 2:
        median = value_at((n + 1) // 2)
    else:
        median = (value_at(n // 2) + value_at(n // 2 + 1)) / 2

    return {
        "rows": rows,
        "mean": weighted_sum / n,
        "median": median,
        "modes": modes,
    }


def build_classes(values):
    """Cria classes pela regra de Sturges e retorna tuplas (limite inf., sup., fi, Fi)."""
    n = len(values)
    minimum, maximum = min(values), max(values)
    if minimum == maximum:
        return [(minimum, maximum, n, n)]

    number_of_classes = max(1, math.ceil(1 + 3.322 * math.log10(n)))
    width = (maximum - minimum) / number_of_classes
    frequencies = [0] * number_of_classes
    for value in values:
        index = min(int((value - minimum) / width), number_of_classes - 1)
        frequencies[index] += 1

    rows = []
    cumulative = 0
    for index, frequency in enumerate(frequencies):
        lower = minimum + index * width
        upper = maximum if index == number_of_classes - 1 else minimum + (index + 1) * width
        cumulative += frequency
        rows.append((lower, upper, frequency, cumulative))
    return rows


def _interpolated_position(rows, n, proportion):
    target = n * proportion
    for index, (lower, upper, frequency, cumulative) in enumerate(rows):
        if frequency and target <= cumulative:
            if lower == upper:
                return lower
            before = rows[index - 1][3] if index else 0
            estimate = lower + ((target - before) / frequency) * (upper - lower)
            return min(max(estimate, lower), upper)
    return rows[-1][1]


def continuous_summary(values):
    """Parte 3: fórmulas de classes agrupadas, sem módulos estatísticos."""
    rows = build_classes(values)
    n = len(values)
    if min(values) == max(values):
        value = values[0]
        return {
            "rows": rows,
            "mean": value,
            "median": value,
            "mode": value,
            "positions": {"Q1": value, "Q3": value, "D2": value, "D7": value,
                          "P15": value, "P22": value, "P63": value, "P70": value},
        }

    weighted_sum = 0.0
    for lower, upper, frequency, _ in rows:
        weighted_sum += ((lower + upper) / 2) * frequency
    mean = weighted_sum / n
    median = _interpolated_position(rows, n, 0.5)

    modal_index = max(range(len(rows)), key=lambda i: rows[i][2])
    lower, upper, modal_frequency, _ = rows[modal_index]
    previous_frequency = rows[modal_index - 1][2] if modal_index else 0
    next_frequency = rows[modal_index + 1][2] if modal_index + 1 < len(rows) else 0
    left = modal_frequency - previous_frequency
    right = modal_frequency - next_frequency
    mode = lower + (left / (left + right)) * (upper - lower) if left + right else (lower + upper) / 2

    proportions = {"Q1": 0.25, "Q3": 0.75, "D2": 0.20, "D7": 0.70,
                   "P15": 0.15, "P22": 0.22, "P63": 0.63, "P70": 0.70}
    positions = {name: _interpolated_position(rows, n, p) for name, p in proportions.items()}
    return {"rows": rows, "mean": mean, "median": median, "mode": mode, "positions": positions}


def _print_table(headers, rows):
    print(" | ".join(headers))
    print("-+-".join("-" * len(header) for header in headers))
    for row in rows:
        print(" | ".join(str(item) for item in row))


def analyze(values):
    """Exibe as três partes do trabalho para a mesma amostra."""
    print(f"\nAmostra carregada: n = {len(values)}")

    print("\nPARTE 1 — DADOS NÃO AGRUPADOS (statistics)")
    result = ungrouped_summary(values)
    print(f"Média: {result['mean']:.2f} | Mediana: {result['median']:.2f} | Moda: {result['mode']:.2f}")

    print("\nPARTE 2 — FREQUÊNCIAS DISCRETAS")
    result = discrete_summary(values)
    _print_table(("Valor (xi)", "fi", "Fi"),
                 [(f"{x:g}", fi, cumulative) for x, fi, cumulative in result["rows"]])
    print(f"Média: {result['mean']:.2f} | Mediana: {result['median']:.2f} | Moda(s): "
          f"{', '.join(f'{value:g}' for value in result['modes'])}")

    print("\nPARTE 3 — FREQUÊNCIAS CONTÍNUAS (Sturges e interpolação de Czuber)")
    result = continuous_summary(values)
    rows = result["rows"]
    width = rows[0][1] - rows[0][0]
    print(f"Número de classes (k): {len(rows)} | Amplitude (h): {width:.2f}")
    class_rows = []
    for index, (lower, upper, fi, cumulative) in enumerate(rows):
        closing = "]" if index == len(rows) - 1 else ")"
        interval = f"[{lower:.2f}, {upper:.2f}{closing}"
        class_rows.append((interval, fi, cumulative))
    _print_table(("Classe", "fi", "Fi"), class_rows)
    print(f"Média: {result['mean']:.2f} | Mediana: {result['median']:.2f} | Moda: {result['mode']:.2f}")
    print("Quartis: " + " | ".join(f"{name} = {result['positions'][name]:.2f}" for name in ("Q1", "Q3")))
    print("Decis: " + " | ".join(f"{name} = {result['positions'][name]:.2f}" for name in ("D2", "D7")))
    print("Percentis: " + " | ".join(
        f"{name} = {result['positions'][name]:.2f}" for name in ("P15", "P22", "P63", "P70")))


def main():
    print("ANALISADOR ESTATÍSTICO — PROBABILIDADE E ESTATÍSTICA")
    print("[1] Digitar dados separados por vírgula")
    print("[2] Carregar arquivo CSV")
    choice = input("Escolha: ").strip()
    try:
        if choice == "1":
            values = parse_values(input("Dados: "))
        elif choice == "2":
            values = load_csv(input("Caminho do CSV: ").strip())
        else:
            raise ValueError("opção inválida; escolha 1 ou 2")
        analyze(values)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Erro: {error}")


if __name__ == "__main__":
    main()
