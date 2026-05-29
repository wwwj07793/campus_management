import re
department_map = {
    
}

def Decorator(judge):
    def decoractor(fn):
        def inner(num):
            if judge == "student_id":
                if re.match(r"^\d{7}$", num):
                    fn(num)
                else:
                    print("该学号不合法")
            elif judge == "age":
                if num > 17 and num < 24:
                    fn(num)
                else:
                    print("该年龄不合法")
            elif judge == "department":
                if num in department_map:
                    fn(num)
                else:
                    print("该院系不合法")
        return inner
    return decoractor
            
        