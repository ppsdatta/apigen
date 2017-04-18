"""
An utility for generating APIs. This tool is written with Python 2/Python 3 compatibility in mind, but some things
may not work in Py 2. It is better to run it outside Docker shell and where the code base actually is. Any Python 3 version
>= 3.4.* should work.
"""
import os
import json
from flask import *

app = Flask(__name__)


def find_url_files(path='.'):
    for roots, dirs, files in os.walk(path):
        for f in files:
            if f == 'urls.py' and roots == path:
                return (roots, dirs, f)

    return None


class FilePaths:
    def __init__(self, start_path='../frontend/api'):
        self.startpath = start_path
        self.modules = []

    def build_url_paths(self):
        data = find_url_files(self.startpath)
        if data:
            self.modules = data[1]

    def get_full_url_path(self, module_name):
        if module_name in self.modules:
            return '{}/{}/urls.py'.format(self.startpath, module_name)


class IO:
    def __init__(self, prompt1='>>', prompt2='>>>', prompt3='|'):
        self.prompts = [prompt1, prompt2, prompt3]

    def aprompt(self, q='', prompt=3):
        return '{} {}'.format(self.prompts[prompt - 1], q)

    def ask_for(self, q='', prompt=3):
        return input(self.aprompt(q, prompt))


class DocuApi:
    def document(self):
        return ''


class ApiState(DocuApi):
    def __init__(self, state='internal'):
        self.state = state

    def document(self):
        return 'state = {}'.format(self.state)


class ApiParams(DocuApi):
    def __init__(self, label='url_parameters'):
        self.param_list = []
        self.label = label

    def add_param(self, name, type, required, desc):
        self.param_list.append((name, type, required, desc))

    def indent(self):
        return '\t\t'

    def document(self):
        template = '{}:\n\t{}\n' + self.indent() + \
                   'optional: {}\n' + self.indent() + \
                   'type: {}\n' + self.indent() + 'description: >\n' + self.indent() + \
                   '\t{}'
        return '\n'.join([template.format(self.label,
                                          p[0],
                                          not p[2],
                                          p[1],
                                          p[3])
                          for p in self.param_list])


class ApiPayloadParams(ApiParams):
    def indent(self):
        return '\t\t\t'


class ApiMethods(DocuApi):
    def __init__(self):
        self.methods_dict = {}

    def add_method(self, method_name):
        self.methods_dict[method_name] = dict(summary='', markdown='', params=None)

    def add_params_for_method(self, method_name, params):
        self.methods_dict[method_name]['params'] = params

    def add_markdown_for_method(self, method_name, mdown):
        self.methods_dict[method_name]['markdown'] = mdown

    def add_summary_for_method(self, method_name, summary):
        self.methods_dict[method_name]['summary'] = summary

    def document(self):
        template = '{}\n\tsummary: {}\n\tmarkdown: |\n\t\t{}\n\t{}'
        return '\n'.join([template.format(k,
                                          self.methods_dict[k]['summary'],
                                          self.methods_dict[k]['markdown'],
                                          self.methods_dict[k]['params'].document()) for k in self.methods_dict.keys()])


class ApiInfo:
    def __init__(self):
        self.version = 0
        self.handler_name = ''
        self.state = None
        self.category = None
        self.methods = None
        self.api_params = None


class ApiProcessor:
    def __init__(self):
        self.paths = FilePaths()
        self.paths.build_url_paths()

    def process(self, api_info):
        print(api_info.state.document())
        print(api_info.api_params.document())
        print(api_info.methods.document())
        url_file = self.paths.get_full_url_path(api_info.category)
        print('modify ', url_file)


processor = ApiProcessor()

@app.route('/')
def home():
    print(processor.paths.modules)
    return render_template('index.html', categories=processor.paths.modules)


@app.route('/generate', methods=['POST'])
def generate():
    print(request.form)
    return 'ok'


if __name__ == '__main__':
    app.run(debug=True)
