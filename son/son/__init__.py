import os
from pathlib import Path
import re
import csv
from flask import Blueprint, current_app, render_template, request, session, Response, abort
import markdown
from bs4 import BeautifulSoup
#from son.catalogue.forms import Form
from son.utils.menu import menu, get_item_title, url_link
from son.utils.logger import LogLevel, Logger

son = Blueprint('son', __name__)
logger = Logger()


def get_content(domain, subdomain=None, indicator=None, use_markdown=True):
    def format_html(html):
        if not use_markdown: return html
        #html = markdown.markdown(html + "\n{: .govuk-body }", extensions=['nl2br', 'attr_list', 'sane_lists'])
        #return html

        if '[Download full dataset (CSV)]' in html:
            file_size = -1
            matches = re.findall('\(.*?\)', html)
            try:
                data_src = f"{os.path.dirname(os.path.realpath(__file__))}/..{matches[1][1: -1]}"
                if Path(data_src).is_file():
                    file_size = os.path.getsize(data_src)
                    with open(data_src, encoding='utf8', errors='ignore') as csv_file:
                        data_table = list(csv.reader(csv_file, delimiter=','))
                        ul = '<ul>'

                        for i in range(len(data_table[0])):
                            item = data_table[0][i].replace('Ind_', 'Indicator ').replace('SEB', 'Socio-economic background').replace('LCI', 'Lower confidence interval').replace('UCI', 'Upper confidence interval').replace('_', ' ')
                            include = False

                            for j in range(len(data_table)):
                                if j > 0:
                                    if data_table[j][i] == "NA" or data_table[j][i] == "N/A" or data_table[j][i] == "N\A":
                                        pass
                                    else:
                                        include = True
                                        break

                            if include:
                                ul += f"<li>{item}</li>"
                            #else:
                            #    ul += f"<li>{item} (NA)</li>"

                        ul += '</ul>'
                        if ul != '<ul></ul>': ul = '<p>This file contains the following variables:</p>' + ul
                        html += ul
            except:
                pass

            if file_size > -1:
                if file_size > 1000000: file_size = f"{int(file_size / 1000000)}MB"
                elif file_size > 1000: file_size = f"{int(file_size / 1000)}KB"
                else: file_size = f"{int(file_size)}B"
                html = html.replace('[Download full dataset (CSV)]', f"[Download full dataset (CSV, {file_size})]")

        html = markdown.markdown(html, extensions=['nl2br', 'attr_list', 'sane_lists'])

        soup = BeautifulSoup(html, 'html.parser')
        for el in soup.find_all('p'):
            if el.has_attr('class'):
                el['class'] = ' '.join(el['class']) + ' govuk-body'
            else:
                el['class'] = 'govuk-body'
        for el in soup.find_all('ul'):
            if el.has_attr('class'):
                el['class'] = ' '.join(el['class']) + ' govuk-list govuk-list--bullet'
            else:
                el['class'] = 'govuk-list govuk-list--bullet'
        for el in soup.find_all('ol'):
            if el.has_attr('class'):
                el['class'] = ' '.join(el['class']) + ' govuk-list'
            else:
                el['class'] = 'govuk-list'
        for el in soup.find_all('a'):
            if el.has_attr('class'):
                el['class'] = ' '.join(el['class']) + ' govuk-link'
            else:
                el['class'] = 'govuk-link'

        return str(soup)

    content = []
    if indicator is not None:
        file_path = f"{os.path.dirname(os.path.realpath(__file__))}/../content/{domain}/{subdomain}/{indicator}.md"
    elif subdomain is not None:
        file_path = f"{os.path.dirname(os.path.realpath(__file__))}/../content/{domain}/{subdomain}.md"
    else:
        file_path = f"{os.path.dirname(os.path.realpath(__file__))}/../content/{domain}.md"

    if Path(file_path).is_file():
        f = open(file_path, 'r')
        current_section = ''
        current_content = ''
        for line in f:
            if len(line) > 2 and line[:2] == '##':
                if current_section != '':
                    content.append(['HTML' if current_section == 'Text' and use_markdown else current_section, format_html(current_content) if current_section == 'Text' else current_content])
                    current_section = ''
                    current_content = ''
                current_section = line[2:].strip()
            elif line.strip() != '':
                if current_content != '': current_content += "\n"
                current_content += line.strip()

        if current_section != '':
            content.append(['HTML' if current_section == 'Text' and use_markdown else current_section, format_html(current_content) if current_section == 'Text' else current_content])

        f.close()

    for index in range(len(content)):
        if content[index][1][:1] == '#':
            current_subsection = ''
            current_subcontent = ''
            current_section = []
            items = content[index][1].split("\n")
            for item in items:
                if len(item) > 1 and item[:1] == '#':
                    if current_subsection != '':
                        if current_subsection.upper() == 'TITLE':
                            current_section.append(['Title', current_subcontent])
                        elif current_subsection.upper() == 'CHART':
                            current_section.append(['Chart', current_subcontent])
                        elif current_subsection.upper() == 'MAP':
                            current_section.append(['Map', current_subcontent])
                        else:
                            current_section.append(['Subtitle', current_subsection])
                            current_section.append(['HTML' if use_markdown else 'Text', format_html(current_subcontent)])

                        current_subsection = ''
                        current_subcontent = ''
                    current_subsection = item[1:].strip()
                elif item.strip() != '':
                    if current_subcontent != '': current_subcontent += "\n"
                    current_subcontent += item.strip()

            if current_subsection.upper() == 'TITLE':
                current_section.append(['Title', current_subcontent])
            elif current_subsection.upper() == 'CHART':
                current_section.append(['Chart', current_subcontent])
            elif current_subsection.upper() == 'MAP':
                current_section.append(['Map', current_subcontent])
            elif current_subsection != '':
                current_section.append(['Subtitle', current_subsection])
                current_section.append(['HTML' if use_markdown else 'Text', format_html(current_subcontent)])

            content[index][1] = current_section

    return content


@son.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pass

    return render_template(
        'homepage/homepage.html',
        menu=menu,
        domain=None,
        subdomain=None,
        indicator=None,
        title='Welcome',
        form=None
    )


@son.route('/social_mobility_by_area', methods=['GET'])
def area_home_page():
    return render_template(
        'area/homepage.html',
        menu=menu,
        area='Social mobility by area',
        domain='social_mobility_by_area',
        selected=[1, 2, 3, 4, 5],
        title=get_item_title('social_mobility_by_area'),
        content=get_content('social_mobility_by_area', use_markdown=False),
        form=None
    )


@son.route('/social_mobility_by_area/<area>', methods=['GET'])
def area_page(area):
    areas = []
    for a in menu['areas']:
        areas.append(url_link(a['name']))
    areas.sort()
    selected = areas.index(area) + 1
    if selected < 3: selected = 3
    if selected > len(areas) - 2: selected = len(areas) - 2

    return render_template(
        'area/area.html',
        menu=menu,
        area=area,
        domain='social_mobility_by_area',
        selected=[selected - 2, selected - 1, selected, selected + 1, selected + 2],
        title=get_item_title(area),
        content=get_content('social_mobility_by_area', use_markdown=False),
        form=None
    )


@son.route('/<domain>', methods=['GET'])
def domain_page(domain):
    return render_template(
        'domain/domain.html',
        menu=menu,
        domain=domain,
        subdomain=None,
        indicator=None,
        title=get_item_title(domain),
        content=get_content(domain, use_markdown=False),
        form=None
    )


@son.route('/<domain>/<subdomain>', methods=['GET'])
def subdomain_page(domain, subdomain):
    return render_template(
        'subdomain/subdomain.html',
        menu=menu,
        domain=domain,
        subdomain=subdomain,
        indicator=None,
        title=get_item_title(subdomain),
        content=get_content(domain, subdomain, use_markdown=False),
        form=None
    )


@son.route('/<domain>/<subdomain>/<indicator>', methods=['GET'])
def indicator_page(domain, subdomain, indicator):
    content = get_content(domain, subdomain, indicator)
    #print(content, flush=True)
    data_src = ''

    data_table = []
    for item in content:
        if item[0] == 'Data Table':
            for index in range(len(item[1])):
                if item[1][index][1] == 'data-src':
                    data_src = f"{os.path.dirname(os.path.realpath(__file__))}/..{item[1][index + 1][1].replace('data-src:', '').strip()}"
                    if Path(data_src).is_file():
                        with open(data_src, encoding='utf8', errors='ignore') as csv_file:
                            data_table = list(csv.reader(csv_file, delimiter=','))

    return render_template(
        'indicator/indicator.html',
        menu=menu,
        domain=domain,
        subdomain=subdomain,
        indicator=indicator,
        title=get_item_title(indicator),
        tabs='Tab' in str(content),
        content=content,
        data_table=data_table,
        form=None
    )


@son.route('/output/', defaults={'page_path': ''}, methods=['GET'])
@son.route('/output/<path:page_path>', methods=['GET'])
def output(page_path):
    #if page_path is None or page_path == '':
    #    page_path = 'index.html'
    #if page_path.endswith('/'):
    #    page_path = page_path + 'index.html'

    response = Response('', 401)
    abort(response)
