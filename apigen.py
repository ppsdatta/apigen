"""
An utility for generating APIs. This tool is written with Python 2/Python 3 compatibility in mind, but some things
may not work in Py 2. It is better to run it outside Docker shell and where the code base actually is. Any Python 3 version
>= 3.4.* should work.
"""
import os
import shutil
import difflib
from flask import *

app = Flask(__name__)

url_file_template1 = '''
api.framework.urlpattern('/v{version}/{category}/', {{
    '{endpoint}': {handle}
}})
'''

url_file_template2 = '''
@allow_http({methods})
def {handler_name}(request, ...):
    """
{state_doc}
\turl_parameters:
{gen_param_doc}
{methods_doc}
    """
    pass

'''


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
        return '\tstate = {}'.format(self.state)


class ApiParams(DocuApi):
    def __init__(self, label='url_parameters'):
        self.param_list = []
        self.label = label

    def add_param(self, name, type, required, desc):
        self.param_list.append((name, type, required, desc))

    def indent(self):
        return '\t\t'

    def document(self):
        template = self.indent() + '{}\n' + \
                   self.indent() + '\toptional: {}\n' + \
                   self.indent() + '\ttype: {}\n' + \
                   self.indent() + '\tdescription: >\n' + \
                   self.indent() + '\t\t{}'
        return ('\n' + self.indent()).join([template.format(
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
        template = '\t{}\n\t\tsummary: {}\n\t\tmarkdown: |\n\t\t\t{}\n\t\tpayload:\n{}'
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
        self.endpoint = None


class ApiProcessor:
    def __init__(self):
        self.paths = FilePaths()
        self.paths.build_url_paths()

    def process(self, api_info):
        url_file = self.paths.get_full_url_path(api_info.category)
        shutil.copyfile(url_file, url_file + '.bak')
        str1 = url_file_template1.format(version=api_info.version,
                                         category=api_info.category,
                                         endpoint=api_info.endpoint,
                                         handle=api_info.handler_name)

        str2 = url_file_template2.format(methods=list(api_info.methods.methods_dict.keys()),
                                         handler_name=api_info.handler_name,
                                         state_doc=api_info.state.document(),
                                         gen_param_doc=api_info.api_params.document(),
                                         methods_doc=api_info.methods.document())
        with open(url_file, 'a') as file:
            file.write(str1)
            file.write('\n')
            file.write(str2)
            file.write('\n')

        new = open(url_file)
        old = open(url_file + '.bak')
        html_diff = difflib.HtmlDiff().make_file(old, new)
        return html_diff


class ApiFormProcessor:
    def __init__(self):
        pass

    def process(self, form):
        methods = self.process_methods(form)
        params = self.process_params(form)

        for m in ['GET', 'POST', 'PUT', 'DELETE']:
            if m in methods.methods_dict:
                methods.add_params_for_method(m, params[m])

        info = ApiInfo()
        info.version = form.get('version', 1)
        info.state = ApiState(form.get('state', 'Live'))
        info.handler_name = form.get('handler', 'handle')
        info.category = form.get('category')
        info.api_params = params['general']
        info.methods = methods
        info.endpoint = form.get('endpoint', '')
        return info

    @staticmethod
    def make_key(name, i):
        return '{}-{}'.format(name, i)

    def process_methods(self, form):
        methods_info = ApiMethods()


        mget = form.get('mget', False)
        mpost = form.get('mpost', False)
        mput = form.get('mput', False)
        mdelete = form.get('mdelete', False)

        if not (mget or mpost or mput or mdelete):
            mget = 'on'

        if mget:
            methods_info.add_method('GET')
            methods_info.add_summary_for_method('GET', form.get('getsummary', ''))
            methods_info.add_markdown_for_method('GET', form.get('getdesc', ''))

        if mpost:
            methods_info.add_method('POST')
            methods_info.add_summary_for_method('POST', form.get('postsummary', ''))
            methods_info.add_markdown_for_method('POST', form.get('postdesc', ''))

        if mput:
            methods_info.add_method('PUT')
            methods_info.add_summary_for_method('PUT', form.get('putsummary', ''))
            methods_info.add_markdown_for_method('PUT', form.get('putdesc', ''))

        if mdelete:
            methods_info.add_method('DELETE')
            methods_info.add_summary_for_method('DELETE', form.get('deletesummary', ''))
            methods_info.add_markdown_for_method('DELETE', form.get('deletedesc', ''))

        return methods_info


    def process_params(self, form):

        def get_opt_param(form, name, i):
            if self.make_key(name, i) in form:
                return form[self.make_key(name, i)]
            else:
                return False

        params_info = dict(general=ApiParams(),
                           GET=ApiPayloadParams(label='payload'),
                           POST=ApiPayloadParams(label='payload'),
                           PUT=ApiPayloadParams(label='payload'),
                           DELETE=ApiPayloadParams(label='payload'))

        try:
            numparams = int(form['numparams'])
        except:
            return params_info

        if numparams > 0:
            for i in range(1, numparams + 1):
                pname = form[self.make_key('pname', i)]
                if not pname:
                    continue

                ptype = form[self.make_key('ptype', i)]
                pdesc = form[self.make_key('pdesc', i)]
                poptional = get_opt_param(form, 'poptional', i)
                pall = get_opt_param(form, 'pall', i)
                pget = get_opt_param(form, 'pget', i)
                ppost = get_opt_param(form, 'ppost', i)
                pput = get_opt_param(form, 'pput', i)
                pdelete = get_opt_param(form, 'pdelete', i)

                if not (pall or pget or ppost or pput or pdelete):
                    pall = 'on'

                if not ptype:
                    ptype = 'String'

                if pall:
                    params_info['general'].add_param(pname, ptype, not poptional, pdesc)
                    continue

                if pget:
                    params_info['GET'].add_param(pname, ptype, not poptional, pdesc)

                if ppost:
                    params_info['POST'].add_param(pname, ptype, not poptional, pdesc)

                if pput:
                    params_info['PUT'].add_param(pname, ptype, not poptional, pdesc)

                if pdelete:
                    params_info['DELETE'].add_param(pname, ptype, not poptional, pdesc)

        return params_info



processor = ApiProcessor()

@app.route('/')
def home():
    print(processor.paths.modules)
    return render_template('index.html', categories=processor.paths.modules)


@app.route('/generate', methods=['POST'])
def generate():
    fp = ApiFormProcessor()
    info = fp.process(request.form)
    try:
        diff = processor.process(info)
    except:
        diff = '<h3>Something went wrong</h3>'
    return diff


if __name__ == '__main__':
    app.run(debug=True)
