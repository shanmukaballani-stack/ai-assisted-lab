def get_valid_mark(subject_no):
    while True:
        try:
            mark = float(input(f"Enter marks for Subject {subject_no}: "))
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
            continue

        if 0 <= mark <= 100:
            return mark

        print("Marks must be between 0 and 100.")


def calculate_grade(average):
    if average >= 90:
        return "A"
    elif average >= 80:
        return "B"
    elif average >= 70:
        return "C"
    elif average >= 60:
        return "D"
    elif average >= 50:
        return "E"
    else:
        return "F"


marks = []
for i in range(1, 6):
    marks.append(get_valid_mark(i))


total = sum(marks)
average = total / len(marks)
grade = calculate_grade(average)

print("\nResults")
print(f"Total marks: {total:.2f}")
print(f"Average marks: {average:.2f}")
print(f"Grade: {grade}")
