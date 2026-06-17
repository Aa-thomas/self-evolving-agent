import json


def test_readjson():
    with open("scripts/jsonfile.json", "r") as file:
        result = json.load(file)

    expected = {"name": "John", "age": 30, "city": "New York"}

    assert result == expected


def test_writejson():
    # this is the data that will be written
    data = {"name": "sathiyajith", "rollno": 56, "cgpa": 8.6, "phone": "9976770500"}

    # this is the act of writing the data
    with open("scripts/write.json", "w") as file:
        json.dump(data, file)

    # this is where we open the file that was written
    with open("scripts/write.json", "r") as file:
        result = json.load(file)

    # this is where we check that the result of opening the file is equal to the data we expected to be written
    assert result == data


def test_validatekeys():
    # open the file and save it to result
    with open("scripts/write.json", "r") as file:
        result = json.load(file)

    expected_name = "sathiyajith"
    expected_rollno = 56
    expected_cgpa = 8.6
    expected_phone = "9976770500"

    assert result["name"] == expected_name

    

