import json

class Event:
    """
    Событие сканирующей прямой (Sweep Line Event). 
    Генерируется при встрече прямой с вершиной полигона.
    """
    def __init__(self, x, y, element_id, prev_node, next_node):
        self.x = x
        self.y = y
        self.element_id = element_id
        
        self.prev_x = prev_node["x"]
        self.prev_y = prev_node["y"]
        self.next_x = next_node["x"]
        self.next_y = next_node["y"]

    def __repr__(self):
        return f"Event(x={self.x}, y={self.y}, el_id={self.element_id})"


class SweepLine:
    def __init__(self, json_filepath):
        self.json_filepath = json_filepath
        self.elements = {}
        self.events = []
        self.element_max_x = {}
        self._load_and_prepare()

    def _load_and_prepare(self):
        """Парсинг JSON и подготовка отсортированной очереди событий."""
        try:
            with open(self.json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Файл {self.json_filepath} не найден. Создайте тестовый JSON.")
            return

        element_id_counter = 0

        # Парсинг
        for cell in data.get("cells", []):
            for shape in cell.get("shapes",[]):
                if shape.get("type") == "polygon":
                    points = shape.get("points",[])
                    if not points:
                        continue
                        
                    if points[0] == points[-1] and len(points) > 1:
                        points = points[:-1]
                        
                    self.elements[element_id_counter] = [{"x": p[0], "y": p[1]} for p in points]
                    element_id_counter += 1

        for el_id, nodes in self.elements.items():
            self.element_max_x[el_id] = max(n["x"] for n in nodes)

        # Генерация событий
        for el_id, nodes in self.elements.items():
            n = len(nodes)
            for i in range(n):
                curr = nodes[i]
                prev_node = nodes[i - 1]
                next_node = nodes[(i + 1) % n]
                self.events.append(Event(curr["x"], curr["y"], el_id, prev_node, next_node))

        # Сначала по X, затем по Y.
        self.events.sort(key=lambda e: (e.x, e.y))

    def run(self, on_point_callback):
        """Запуск сканирующей прямой с инъекцией логики (callback)."""
        if not self.events:
            return

        active_elements = set()
        violations =[]
        reported_pairs = set()

        for i, event in enumerate(self.events):
            # Удаляет из активного множества полигоны, оставшиеся позади прямой
            to_remove =[el for el in active_elements if self.element_max_x[el] < event.x]
            for el in to_remove:
                active_elements.remove(el)

            # Добавляет текущего элемента в активное множество
            active_elements.add(event.element_id)

            # Инъекция функции поиска нарушений
            violation = on_point_callback(event, i, self.events, active_elements)
            
            # Защита от дублирования отчетов
            if violation:
                pair = tuple(sorted([violation["source_element"], violation["target_element"]]))
                if pair not in reported_pairs:
                    violations.append(violation)
                    reported_pairs.add(pair)

        self._save_results(violations)
        print(f"Анализ завершен. Найдено нарушений 'Касание в точке': {len(violations)}")

    def _save_results(self, violations):
        output = {"detailed_predictions": violations}
        with open("student_predictions.json", "w", encoding='utf-8') as f:
            json.dump(output, f, indent=2)


"""
Реализует поиск нарушений "Касание полигонов в одной точке".
"""
def detect_point_contact(event, current_index, all_events, active_elements):
    # Извлекает из события координаты отрезков
    def get_intervals(evt, axis):
        intervals =[]
        if axis == 'y':
            if evt.prev_x == evt.x: intervals.append((min(evt.y, evt.prev_y), max(evt.y, evt.prev_y)))
            if evt.next_x == evt.x: intervals.append((min(evt.y, evt.next_y), max(evt.y, evt.next_y)))
        elif axis == 'x':
            if evt.prev_y == evt.y: intervals.append((min(evt.x, evt.prev_x), max(evt.x, evt.prev_x)))
            if evt.next_y == evt.y: intervals.append((min(evt.x, evt.next_x), max(evt.x, evt.next_x)))
        return intervals

        ###Ваш код
        
        return {
            "source_element": event.element_id,
            "target_element": neighbor.element_id,
            "violation_probability": 1.0,
            "status": "CRITICAL"
        }
    
    return None

if __name__ == "__main__":
    input_file = "test_schema_unlabeled.json"
    print(f"Запуск алгоритма сканирующей прямой для файла: {input_file}")
    
    sweepLine = SweepLine(input_file)
    sweepLine.run(on_point_callback=detect_point_contact)