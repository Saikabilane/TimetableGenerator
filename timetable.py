import streamlit as st
import pandas as pd
import random
import copy
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()
st.title("Timetable Generator")

#Getting inputs
bufferz = True
NUM_TIMESLOTS = 40

uploadedFile = st.file_uploader("Upload a CSV for Theory and Lab classes", type=['csv'], accept_multiple_files=False, key="fileUploader")
if uploadedFile is not None:
    file = pd.read_csv(uploadedFile)
    try:
        courses = file['courseCode']
        faculty = file['empId']
        course_type = file['courseType']
        classes = file['classId']
        hoursPerWeek = file['hours/week']
    except:
        bufferz = False
        st.warning("The given CSV is invalid")
else:
    bufferz = False
    st.warning("Upload a valid CSV file to continue")

electivesFile = st.file_uploader("Upload a CSV for Electives", type=['csv'], accept_multiple_files=False, key="electivesUploader")
if electivesFile is not None:
    elective_file = pd.read_csv(electivesFile)
    try:
        elect_class = elective_file['Class Name']
        elect_subs = elective_file['Electives']
    except:
        bufferz = False
        st.warning("The given CSV is invalid")
else:
    bufferz = False
    st.warning("Upload a valid CSV file to continue")

visitingFile = st.file_uploader("Upload a CSV for Blocking classes", type=['csv'], accept_multiple_files=False, key="visitingUploader")
if visitingFile is not None:
    visiting_file = pd.read_csv(visitingFile)
    try:
        visit_facs = list(visiting_file["faculty code"])
        visit_class = list(visiting_file["Class Name"])
        visit_subCode = list(visiting_file["subject code"])
        visit_time = list(visiting_file["Timeslot"])
    except:
        bufferz = False
        st.warning("The given CSV is invalid")
else:
    bufferz = False
    st.warning("Upload a valid CSV file to continue")

teacherFile = st.file_uploader("Upload a CSV for Blocking Teachers", type=['csv'], accept_multiple_files=False, key="teacherUploader")
if teacherFile is not None:
    teacher_file = pd.read_csv(teacherFile)
    try:
        teacher_facs = list(teacher_file["faculty code"])
        teacher_time = list(teacher_file["Timeslot"])
    except:
        bufferz = False
        st.warning("The given CSV is invalid")
else:
    bufferz = False
    st.warning("Upload a valid CSV file to continue")

facBlock = {}
for fac in range(len(teacher_facs)):
    if teacher_facs[fac] not in facBlock.keys():
        facBlock[teacher_facs[fac]] = [teacher_time[fac]]
    else:
        facBlock[teacher_facs[fac]].append(teacher_time[fac])

#Creating Total period counts per day
period_times = {}
x = NUM_TIMESLOTS//5
days = ['M', 'T', 'W', 'TH', 'F']
count = 0
for day in days:
    for _ in range(1,x+1):
        count += 1
        temp_str = day+str(_)
        period_times[count] = temp_str

################################################################
#Staff checking
def faccheck(timetable):
    staffid = []
    stafftime = {}
    conflict=[]
    classnot=[]
    def allocate(sub,staff,clas,i):
        f=["free" for _ in range(40)]
        if staff not in staffid:
            stafftime[staff]=f
            staffid.append(staff)
            allocate(sub,staff,clas,i)
        else:
            if stafftime[staff][i]=="free":
                stafftime[staff][i]=[sub,clas]
            else:
                conflict.append("1")
                classnot.append([sub,staff,clas,i])
    def create():
        for i,k in timetable.items():
            m=0
            for j in k:
                if j!='Free Period':
                    for t in range(1,len(j)):
                        allocate(j[0],j[t],i,m)
                m+=1
    create()
    return classnot

def facTime(timetable):
    staffid = []
    stafftime = {}
    conflict=[]
    classnot=[]
    def allocate(sub,staff,clas,i):
        f=["free" for _ in range(40)]
        if staff not in staffid:
            stafftime[staff]=f
            staffid.append(staff)
            allocate(sub,staff,clas,i)
        else:
            if stafftime[staff][i]=="free":
                stafftime[staff][i]=[sub,clas]
            else:
                conflict.append("1")
                classnot.append([sub,staff,clas,i])
    def create():
        for i,k in timetable.items():
            m=0
            for j in k:
                if j!='Free Period':
                    for t in range(1,len(j)):
                        allocate(j[0],j[t],i,m)
                m+=1
    create()
    return stafftime

#Returns the list of classes a week for a given class name
def class_courses(Class):
    clsList = []
    check = []
    for _ in range(len(classes)):
        if classes[_] == Class and courses[_] not in check:
            check.append(courses[_])
            h_w = hoursPerWeek[_].split('+')
            h_w = [int(x) for x in h_w]
            hpw = sum(h_w)
            for i in range(hpw):
                clsList.append([courses[_], faculty[_]])
        elif classes[_] == Class and courses[_] in check:
            for i in range(len(clsList)):
                if clsList[i][0] == courses[_]:
                    clsList[i].append(faculty[_])
    for clss in range(len(elect_class)):
        if elect_class[clss] == Class:
            fin_list = [elect_subs[clss]]
            elective_list = elect_subs[clss].split('/')
            subs = [x[0] for x in clsList]
            x = subs.count(elective_list[0])
            for k in range(len(courses)):
                if courses[k] in elective_list:
                    courses[k] = "BUFFER"
            for i in range(len(subs)):
                if subs[i] in elective_list:
                    fin_list.extend(clsList[i][1:])
                    clsList[i] = "BUFFER"
            while clsList.count("BUFFER") > x:
                clsList.remove("BUFFER")
            for i in range(len(fin_list)):
                if fin_list.count(fin_list[i]) > 1 and fin_list[i] != 'o':
                    fin_list[i] = 'o'
            while 'o' in fin_list:
                fin_list.remove('o')
            for cls in range(len(clsList)):
                if clsList[cls] == "BUFFER":
                    clsList[cls] = fin_list
            for cls in range(len(courses)):
                if courses[cls] == "BUFFER":
                    courses[cls] = elect_subs[clss]
    free = 40 - int(len(clsList))
    clsList.extend(["Free Period"]*int(free))
    clsList = clsList[:40]
    return clsList

# Parameters for the genetic algorithm
POPULATION_SIZE = 25
NUM_GENERATIONS = 25
MUTATION_RATE = 0.1
#NUM_CLASSES = len(set(classes))
WORKING_DAYS = 5

#To check if the given class is lab or theory
def isLabClasses(course):
    if course != "Free Period":
        for _ in range(len(courses)):
            if courses[_] == course[0]:
                courseType = course_type[_]
                break
    else:
        courseType = "Free Period"
    return courseType

#to get the lab split hours per week
def labComponent(course):
    x = course[0]
    val = False
    for i in range(len(hoursPerWeek)):
        if courses[i] == x and int(hoursPerWeek[i][-1]) != 0 and course_type[i] == "Theory":
            val = True
    return val

# Fitness function
def fitness(timetable):
    fitness_score = 0
    total_slots = 0
    for cls, schedule in timetable.items():
        if len(schedule) != NUM_TIMESLOTS:
            fitness_score += 100
        else:
            total_slots += NUM_TIMESLOTS
        expected = class_courses(cls)
        expected_Courses = [x for x in expected if x != "Free Period"]
        obtained_Courses = [x for x in schedule if x != "Free Period"]
        if sorted(expected_Courses) != sorted(obtained_Courses):
            fitness_score += 100
    if total_slots == NUM_TIMESLOTS*len(set(classes)):
        fitness_score += len(faccheck(timetable))
        for cls, schedule in timetable.items():
            for _ in range(NUM_TIMESLOTS):
                if isLabClasses(schedule[_]) == "Lab":
                    consecutive_class = schedule[_+1] if _%2==0 else schedule[_-1]
                    if consecutive_class != schedule[_]:
                        fitness_score += 1
    return fitness_score

def convert_to_dataframe(timetable):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5", "Period 6", "Period 7", "Period 8"]
    
    df_dict = {"Class": []}
    for day in days:
        for period in periods:
            df_dict[f"{day} - {period}"] = []

    for class_name, schedule in timetable.items():
        df_dict["Class"].append(class_name)
        for i, period in enumerate(schedule):
            day_index = i // 8
            period_index = i % 8
            day_period_key = f"{days[day_index]} - {periods[period_index]}"
            df_dict[day_period_key].append(period)
    
    return pd.DataFrame(df_dict)

#To create a ordered arrangement of classes making labs as a pair
def chunk(clsName, schedule):
    mon = ["free" for _ in range(8)]
    tue = ["free" for _ in range(8)]
    wed = ["free" for _ in range(8)]
    thu = ["free" for _ in range(8)]
    fri = ["free" for _ in range(8)]
    week = [mon, tue, wed, thu, fri]
    dupe = [mon, tue, wed, thu, fri]
    if clsName in visit_class:
        for _ in range(len(visit_class)):
            if clsName == visit_class[_]:
                x = [i for i in schedule if i[0] == visit_subCode[_] and visit_facs[_] in i[1:]]
                slot = int(visit_time[_])%8
                dayi = int(visit_time[_])//8
                day = dupe[dayi]
                day[slot] = x[0]
                schedule.remove(x[0])
    freeCount = schedule.count("Free Period")
    dupe = [mon, tue, wed, thu, fri]
    if freeCount >= 5:
        for days in week:
            if days[-1] == "free":
                days[-1] = "Free Period"
            else:
                freeCount += 1
        freeCount -= 5
    else:
        while freeCount:
            day = random.choice(dupe)
            day[-1] = "Free Period"
            freeCount -= 1
            dupe.remove(day)
    dupe = [mon, tue, wed, thu, fri]
        
    dupe = [mon, tue, wed, thu, fri]
    crsList = [x for x in schedule if isLabClasses(x) == "Lab"]
    while crsList:
        randomClass = random.choice(crsList)
        classCount = crsList.count(randomClass)
        buffer = 0
        dupe = [mon, tue, wed, thu, fri]
        for labs in range(len(courses)):
            if courses[labs] == randomClass[0]:
                break
        avoid = []
        ds = randomClass[1:]
        for d in ds:
            if d in facBlock.keys():
                avoid.extend(facBlock[d])
        if hoursPerWeek[labs] == '2+2' or hoursPerWeek[labs] == '2+0':
            while buffer < classCount:
                day = random.choice(dupe)
                slots = [x for x in range(0,8,2) if day[x] == "free" and day[x+1] == "free" and x not in avoid and x+1 not in avoid]
                if slots:
                    x = random.choice(slots)
                    day[x], day[x+1] = randomClass, randomClass
                    crsList.remove(randomClass)
                    crsList.remove(randomClass)
                    dupe.remove(day)
                    buffer += 2
        elif hoursPerWeek[labs] == '4+0':
            while buffer < classCount:
                day = random.choice(dupe)
                slots = [x for x in range(0,8,4) if day[x] == "free" and day[x+1] == "free" and day[x+2] == "free" and day[x+3] == "free" and x not in avoid and x+1 not in avoid and x+2 not in avoid and x+3 not in avoid]
                if slots:
                    x = random.choice(slots)
                    day[x], day[x+1], day[x+2], day[x+3] = randomClass, randomClass, randomClass, randomClass
                    crsList.remove(randomClass)
                    crsList.remove(randomClass)
                    crsList.remove(randomClass)
                    crsList.remove(randomClass)
                    dupe.remove(day)
                    buffer += 4
    final = []
    for i in week:
        final.extend(i)
    crsList = [x for x in schedule if isLabClasses(x) != "Lab" and isLabClasses(x) != "Free Period" and isLabClasses(x) != "Visiting"]
    crsSlot = [x for x in range(40) if final[x] == "free"]
    while crsList:
        randomClass = random.choice(crsList)
        randomSlot = random.choice(crsSlot)
        avoid = []
        ds = randomClass[1:]
        for d in ds:
            if d in facBlock.keys():
                avoid.extend(facBlock[d])
        if randomSlot in avoid:
            continue
        final[randomSlot] = randomClass
        crsList.remove(randomClass)
        crsSlot.remove(randomSlot)
    if final.count("free") == freeCount:
        for _ in range(len(final)):
            if final[_] == "free":
                final[_] = "Free Period"    
    return final
        
#initializing population
def create_individual():
    timetable = {}
    for cls in list(set(classes)):
        timetable[cls] = chunk(cls, class_courses(cls))
    return timetable

def create_population():
    return [create_individual() for _ in range(POPULATION_SIZE)]

# Theory Crossover
def crossover1(parent1):
    child = {}
    total_slots1 = 0
    child = copy.deepcopy(parent1)
    for cls, schedule in parent1.items():
        total_slots1 += len(schedule)
    for clss, schedule in child.items():
        if total_slots1 == NUM_TIMESLOTS*len(set(classes)):
            compare = []
            if cls in visit_class:
                for i in range(len(visit_class)):
                    if cls == visit_class[i]:
                        compare.append(int(visit_time[i]))
            for _ in range(NUM_TIMESLOTS):
                teachers = schedule[_][1:]
                avoid = []
                for teacher in teachers:
                    if teacher in facBlock.keys():
                        avoid.extend(facBlock[teacher])
                if _ in visit_time:
                    continue
                if isLabClasses(schedule[_]) == "Lab":
                    continue
                x = []
                for cls in list(set(classes)):
                    if child[cls][_] != "Free Period":
                        all = child[cls][_][1:]
                        x.extend(all)
                y = set(x)
                if len(x) != len(y):
                    if x.count(child[clss][_][1]) > 1:
                        if isLabClasses(child[clss][_]) == "Theory":
                            for k in range(NUM_TIMESLOTS):
                                if k in avoid:
                                    continue
                                if k in compare:
                                    continue
                                teachers2 = schedule[k][1:]
                                avoid2 = []
                                for teacher2 in teachers2:
                                    if teacher2 in facBlock.keys():
                                        avoid2.extend(facBlock[teacher2])
                                if _ in avoid2:
                                    continue
                                a = []
                                for cls in list(set(classes)):
                                    if child[cls][k] != "Free Period":
                                        alli = child[cls][k][1:]
                                        a.extend(alli)
                                b = set(a)
                                if a.count(child[clss][k]) == 1:
                                    continue
                                if k != _ and child[clss][k][1] not in x and isLabClasses(child[clss][k]) == 'Theory':
                                    child[clss][k], child[clss][_] = child[clss][_], child[clss][k]
                                    break
    return child

# Lab crossover
def crossover2(individual1):
    total_slots1 = 0
    individual = copy.deepcopy(individual1)
    for schedule in individual.values():
        total_slots1 += len(schedule)
    for cls, schedule in individual.items():
        if total_slots1 == NUM_TIMESLOTS*len(set(classes)):
            compare = []
            if cls in visit_class:
                for i in range(len(visit_class)):
                    if cls == visit_class[i]:
                        compare.append(int(visit_time[i]))
            for _ in range(NUM_TIMESLOTS):
                teachers = schedule[_][1:]
                avoid = []
                for teacher in teachers:
                    if teacher in facBlock.keys():
                        avoid.extend(facBlock[teacher])
                if _ in compare:
                    continue
                if isLabClasses(schedule[_]) == "Visiting":
                    continue
                x = []
                for clss in list(set(classes)):
                    if individual[clss][_] != "Free Period":
                        all = individual[clss][_][1:]
                        x.extend(all)
                y = set(x)
                if len(x) != len(y):
                    if isLabClasses(individual[cls][_]) == "Lab":
                        condition = False
                        for m in range(len(individual[cls][_])):
                            if x.count(individual[cls][_][m]) > 1:
                                condition = True
                        if condition:
                            if individual[cls][(int(_//4)*4)] == individual[cls][(int(_//4)*4)+1] and individual[cls][(int(_//4)*4)+1] == individual[cls][(int(_//4)*4)+2] and individual[cls][(int(_//4)*4)+2] == individual[cls][(int(_//4)*4)+3]:
                                lst = [k for k in range(0,NUM_TIMESLOTS,4) if k != int(_//4)*4 and k not in compare and k+1 not in compare and k+2 not in compare and k+3 not in compare and k not in avoid and k+1 not in avoid and k+2 not in avoid and k+3 not in avoid]
                                chosen = random.choice(lst)
                                individual[cls][(int(_//4)*4):(int(_//4)*4)+4],individual[cls][chosen:chosen+4] = individual[cls][chosen:chosen+4],individual[cls][(int(_//4)*4):(int(_//4)*4)+4]
                                break
                            elif individual[cls][(int(_//2)*2)] == individual[cls][(int(_//2)*2)+1]:
                                lst = [k for k in range(0,NUM_TIMESLOTS,2) if k != int(_//2)*2 and k not in compare and k+1 not in compare and k not in avoid and k+1 not in avoid]
                                chosen = random.choice(lst)
                                individual[cls][(int(_//2)*2):(int(_//2)*2)+2],individual[cls][chosen:chosen+2] = individual[cls][chosen:chosen+2],individual[cls][(int(_//2)*2):(int(_//2)*2)+2]
                                break
    return individual

#Mutation
def mutate(individual):
    individual1 = copy.deepcopy(individual)
    for cls, schedule in individual1.items():
        if random.random() < MUTATION_RATE:
            individual1[cls] = chunk(cls, schedule)
    individual1 = crossover2(individual1)
    individual1 = crossover1(individual1)
    return individual1

# Main genetic algorithm
def genetic_algorithm():

    population = create_population()
    population = sorted(population, key=fitness, reverse=False)

    for generation in range(NUM_GENERATIONS):
        population = sorted(population, key=fitness, reverse=False)
        new_population = population[:10]
        for _ in range(10):
            parent1 = new_population[_]
            child1 = crossover2(parent1)
            child = crossover1(child1)
            child2 = mutate(child)
            new_population.append(child)
            new_population.append(child1)
            new_population.append(child2)
        new_population = sorted(new_population, key=fitness, reverse=False)
        
        population = new_population
        population = sorted(population, key=fitness, reverse=False)
        best_timetable = population[0]
        print(f"Generation {generation}: Best Fitness = {fitness(best_timetable)}")
        if fitness(best_timetable) == 0:
            break

    return best_timetable

######################

def prepare_timetable_for_display(timetable):
    timetable_df = pd.DataFrame(timetable)
    timetable_df = timetable_df.applymap(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else str(x))
    return timetable_df

def pdf_generator(timetable):
    formatted = {}
    for cls, schedule in timetable.items():
        new = []
        for i in range(0, 40, 8):
            new.append(schedule[i:i+8])
        formatted[cls] = new
    return formatted

def generate_html_timetable(timetable):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5", "Period 6", "Period 7", "Period 8"]
    
    html_output = """<style>
      .tt th { padding: 15px; text-align: left; background-color: #0eb6cc; color: white; }
      .tt td { padding: 15px; text-align: left; background-color: #f2f2f2; color: black; }
      .tt tr:hover td { background-color: #ddd; }
    </style>"""
    
    for class_name, schedule in timetable.items():
        html_output += f"<h2>Timetable for {class_name}</h2>\n"
        html_output += "<table class='tt' border='1' cellpadding='5' cellspacing='0'>\n"
        html_output += "  <tr><th>Day</th>" + "".join([f"<th>{p}</th>" for p in periods]) + "</tr>\n"
        
        for i, day in enumerate(days):
            html_output += f"  <tr><td>{day}</td>" + "".join([f"<td>{p}</td>" for p in schedule[i]]) + "</tr>\n"
        
        html_output += "</table>\n<br/>\n"
    
    return html_output

def give_exceptions(timetable):
    exceptions = faccheck(timetable)
    f = open('exceptions.txt', 'w')
    for ex in exceptions:
        f.writelines(f"{ex[1]} ,{ex[0]} ,{ex[2]} {period_times[ex[3]]} \n")
    f.close()

def creat(table, filename):
    tabl = pdf_generator(table)
    html_content = generate_html_timetable(tabl)
    return html_content

if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

def disable_button():
    st.session_state.button_clicked = True

if bufferz:
    if st.button("Generate Timetable", on_click= disable_button, disabled=st.session_state.button_clicked):
        st.info("Generating timetable. Please wait...")
        
        # Generate the timetable and staff timetable
        timetable = genetic_algorithm()
        staff_timetable = facTime(timetable)
        
        # Submit tasks to the executor properly
        future = executor.submit(prepare_timetable_for_display, timetable)
        staffs = executor.submit(prepare_timetable_for_display, staff_timetable)
        
        with st.spinner("Working on the timetable..."):
            # Retrieve the results from the futures
            timetable_df = future.result()
            staff_df = staffs.result()
        
        st.success("Timetable generated successfully!")
        st.subheader(f"The Following Timetable has the fitness of {fitness(timetable)}.")

        class_tt = creat(timetable, "classTT.html")
        staff_tt = creat(staff_timetable, "staffTT.html")
        
        combined_tt = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Combined Timetables</title>
            </head>
            <body>
                <h1>TIMETABLE GENERATOR</h1><br>
                <cite>Use Ctrl+P to save the page as pdf</cite><br>
                <h1>Class Timetable</h1>
                {class_tt}
                <hr>
                <h1>Staff Timetable</h1>
                {staff_tt}
                <cite>Use Ctrl+P to save the page as pdf</cite>
            </body>
            </html>
            """

        st.download_button(
            label="Download Class and Staff Timetable here.",
            data=combined_tt,
            file_name="Timetable.html",
            mime="html"
        )

        # Display the timetables
        st.write("Class Timetable")
        st.dataframe(timetable_df)
        st.write("Staff Timetable")
        st.dataframe(staff_df)
        
        # Option to download as CSV
        csv1 = timetable_df.to_csv(index=False)
        csv2 = staff_df.to_csv(index=False)

        
        conflicts = faccheck(timetable)
        if len(conflicts) != 0: 
            st.write("Classes that are alloted wrongly are as follows:")
            st.write("Course Code - Faculty code - Class name - Timeslot")
            for conflict in conflicts:
                st.write(f"{conflict}")