import os, re
import openapiart.goserver.string_util as util
import openapiart.goserver.generator_context as ctx
from openapiart.goserver.writer import Writer

class GoServerInterfaceGenerator(object):

    def __init__(self, context: ctx.GeneratorContext):
        self._indent = '\t'
        self._models_prefix = context.models_prefix
        self._root_package = context.module_path
        self._package_name = "interfaces"
        self._ctx = context
        self._output_path = os.path.join(context.output_path, 'interfaces')
    
    def generate(self):
        self._write_interfaces()

    def _write_interfaces(self):
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)
        for ctrl in self._ctx.controllers:
            self._write_interface(ctrl)

    def _write_interface(self, ctrl: ctx.Controller):
        filename = ctrl.yamlname.lower() + "_interface.go"
        fullname = os.path.join(self._output_path, filename)
        w = Writer(self._indent)
        self._write_header(w)
        self._write_import(w)
        self._write_path_param_const(w, ctrl)
        self._write_controller_interface(w, ctrl)
        self._write_servicehandler_interface(w, ctrl)
        with open(fullname, 'w') as file:
            print(f"Interface: {fullname}")
            for line in w.strings:
                file.write(line + '\n')
            pass
        pass

    def _write_header(self, w: Writer):
        w.write_line(
            "// This file is autogenerated. Do not modify",
            f"package {self._package_name}",
            ""
        )

    def _write_import(self, w: Writer):
        w.write_line(
            "import ("
        ).push_indent(
        ).write_line(
            '"net/http"',
            f'"{self._root_package}/httpapi"',
            f'{re.sub("[.]", "", self._ctx.models_prefix)} "{self._ctx.models_path}"',
        ).pop_indent(
        ).write_line(
            ")",
            ""
        )

    def _write_path_param_const(self, w: Writer, ctrl: ctx.Controller):
        params: [str] = []
        for r in ctrl.routes:
            for param in r.route_parameters:
                if param not in params:
                    params.append(param)
        if len(params) > 0:
            w.write_line("const (")
            w.push_indent()
            for param in params:
                w.write_line(f"{util.pascal_case(ctrl.yamlname)}{util.pascal_case(param)} = \"{param}\"")
            w.pop_indent()
            w.write_line(")", "")
        pass

    def _write_route_description(self, w: Writer, r: ctx.ControllerRoute):
        w.write_line("/*")
        w.write_line(f"{r.operation_name}: {r.method} {r.url}")
        w.write_line("Description: " + r.description)
        w.write_line("*/")

    def _write_controller_interface(self, w: Writer, ctrl: ctx.Controller):
        w.write_line(
            f"type {ctrl.controller_name} interface {{",
        )
        w.push_indent()
        w.write_line(
            "Routes() []httpapi.Route",
        )
        for r in ctrl.routes:
            # self._write_route_description(w, r)
            w.write_line(
                f"{r.operation_name}(w http.ResponseWriter, r *http.Request)",
            )
        w.pop_indent()
        w.write_line(
            "}",
            ""
        )

    def _write_servicehandler_interface(self, w: Writer, ctrl: ctx.Controller):
        w.write_line(
            f"type {ctrl.service_handler_name} interface {{",
        )
        w.push_indent()
        w.write_line(
            f"GetController() {ctrl.controller_name}",
        )
        for r in ctrl.routes:
            self._write_route_description(w, r)
            full_responsename = r.full_responsename
            request_body: Component = r.requestBody()
            if request_body != None:
                full_requestname = request_body.full_model_name
                w.write_line(
                    f"{r.operation_name}(rbody {full_requestname}, r *http.Request) {full_responsename}"
                )
            else:
                w.write_line(
                    f"{r.operation_name}(r *http.Request) {full_responsename}"
                )
        w.pop_indent()
        w.write_line(
            "}",
            ""
        )


