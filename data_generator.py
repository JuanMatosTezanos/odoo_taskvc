from os import path
from os import remove
import random
import base64

n_technologies = 0

def random_technologies():
    n_t = random.randint(1, n_technologies)
    tech = []
    cont = 0

    while cont < n_t:
        random_tech = random.randint(1, n_technologies)
        tech_id = "technology_" + str(random_tech)
        if not tech_id in tech:
            tech.append(tech_id)
            cont += 1
    return tech

def format_random_technologies():
    tech = random_technologies()
    tech_string = "[(6,0,["
    for i in range(len(tech)):
        tech_string += "ref(\'"+tech[i]+"\')"
        if i < len(tech) - 1:
            tech_string += ","
    tech_string += "])]"
    return tech_string




def delete_file(file):
    if path.exists(file):
        remove(file)


def write_text(text,file):
    with open(file, 'a') as f:
        f.write(text)


def write_dev(line, demo_file):
    write_text(f'<record id= \'dev_{line[0]}\' model =\'res.partner\'>', demo_file)
    write_text(f'<field name= \'name\'>{line[1]}</field>', demo_file)
    write_text(f'<field name= \'last_login\' eval=\"(datetime.now().strftime(\'%Y-%m-%d\'))\"></field>', demo_file)
    write_text(f'<field name= \'access_level\'>{line[2]}</field>', demo_file)
    write_text(f'<field name= \'is_dev\'>True</field>', demo_file)
    write_text(f'<field name= \'technologies\' eval="{format_random_technologies()}"></field>', demo_file)
    write_text(f'</record>', demo_file)

def write_project(line, demo_file):
    write_text(f'<record id= \'project_{line[0]}\' model =\'manage.project\'>', demo_file)
    write_text(f'<field name= \'name\'>{line[1]}</field>', demo_file)
    write_text(f'</record>', demo_file)

def write_history(line, demo_file):
    write_text(f'<record id= \'history_{line[0]}\' model =\'manage.history\'>', demo_file)
    write_text(f'<field name= \'name\'>{line[1]}</field>', demo_file)
    #<field name='project' ref='project_1'></field>
    write_text(f'<field name= \'project\' ref= \'project_1\'></field>', demo_file)
    write_text(f'</record>', demo_file)




def devs_generator(source, demo_file):
    delete_file(demo_file)
    write_text('<odoo><data>', demo_file)
    with open(source) as file:
        for line in file:
            line = line.split(',')
            write_dev(line,demo_file)
    write_text('</data></odoo>', demo_file)

def project_generator(source, demo_file):
    delete_file(demo_file)
    write_text('<odoo><data>', demo_file)
    with open(source) as file:
        for line in file:
            line = line.split(',')
            write_project(line,demo_file)
    write_text('</data></odoo>', demo_file)

def history_generator(source, demo_file):
    delete_file(demo_file)
    write_text('<odoo><data>', demo_file)
    with open(source) as file:
        for line in file:
            line = line.split(',')
            write_history(line,demo_file)
    write_text('</data></odoo>', demo_file)

def technologies_generator(source, demo_file):
    global n_technologies
    delete_file(demo_file)
    write_text('<odoo><data>', demo_file)
    with open(source) as file:
        for line in file:
            line = line.strip().split(',')
            n_technologies += 1
            write_technology(line,demo_file)
    write_text('</data></odoo>', demo_file)

def write_technology(line, demo_file):
    write_text(f'<record id= \'technology_{line[0]}\' model =\'manage.technology\'>', demo_file)
    write_text(f'<field name= \'name\'>{line[1]}</field>', demo_file)


    image = open("tech_images/"+line[1]+".png", "rb")
    b64_string = base64.b64encode(image.read()).decode('utf-8')

    write_text(f'<field name= \'photo\'>{b64_string}</field>', demo_file)
    write_text(f'</record>', demo_file)   



project_generator(
    'csv/projects.csv',
    'dev_addons/manage/demo/projects.xml'
)

history_generator(
    'csv/histories.csv',
    'dev_addons/manage/demo/histories.xml'
)


technologies_generator(
    'csv/technologies.csv',
    'dev_addons/manage/demo/technologies.xml'
)

devs_generator(
    'csv/devs.csv',
    'dev_addons/manage/demo/devs.xml'
)



