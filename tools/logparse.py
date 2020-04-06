import re

regex = re.compile(r"[\[][a-zA-Z]*(\s)*[a-zA-Z0-9]*[\]]")
people = []

with open("requests.log") as f:
    for line in f:
        result = regex.search(line)
        if result:
            # print(dir(result))
            # print(result[0])
            people.append(result[0])

people = list(set(people))
print("\n".join(people))
print("Length:", len(people))

