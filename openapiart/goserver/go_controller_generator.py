import os, re
import openapiart.goserver.string_util as util
import openapiart.goserver.generator_context as ctx
from openapiart.goserver.writer import Writer

class GoServerControllerGenerator(object):

    def __init__(self, ctx: ctx.GeneratorContext):
        self._indent = '\t'
        self._root_package = ctx.module_path
        self._package_name = "controllers"
        self._ctx = ctx
        self._output_path = os.path.join(ctx.output_path, 'controllers')
    
    def generate(self):
        self._write_controllers()

    def _write_controllers(self):
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)
        for ctrl in self._ctx.controllers:
            self._write_controller(ctrl)

    def _write_controller(self, ctrl: ctx.Controller):
        filename = ctrl.yamlname.lower() + "_controller.go"
        fullname = os.path.join(self._output_path, filename)
        w = Writer(self._indent)
        self._write_header(w)
        self._write_import(w)
        self._write_controller_struct(w, ctrl)
        self._write_newcontroller(w, ctrl)
        self._write_routes(w, ctrl)
        self._write_methods(w, ctrl)
        with open(fullname, 'w') as file:
            print(f"Controller: {fullname}")
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
            '"io/ioutil"',
            '"net/http"',
            f'"{self._root_package}/httpapi"',
            f'"{self._root_package}/httpapi/interfaces"',
            f'{re.sub("[.]", "", self._ctx.models_prefix)} "{self._ctx.models_path}"',

            # f'"{self._root_package}/models"',
        ).pop_indent(
        ).write_line(
            ")",
            ""
        )

    def _struct_name(self, ctrl: ctx.Controller) -> str:
        return util.camel_case(ctrl.controller_name)
    
    def _write_controller_struct(self, w: Writer, ctrl: ctx.Controller):
        w.write_line(
            f"type {self._struct_name(ctrl)} struct {{",
        )
        w.push_indent()
        w.write_line(
            f"handler interfaces.{ctrl.service_handler_name}",
        )
        w.pop_indent()
        w.write_line(
            "}",
            ""
        )
        pass

    def _write_newcontroller(self, w: Writer, ctrl: ctx.Controller):
        w.write_line(
            f"func NewHttp{ctrl.controller_name}(handler interfaces.{ctrl.service_handler_name}) interfaces.{ctrl.controller_name} {{",
        ).push_indent()
        w.write_line(
            f"return &{self._struct_name(ctrl)}{{handler}}",
        ).pop_indent()
        w.write_line(
            "}",
            ""
        )
        pass

    def _write_routes(self, w: Writer, ctrl: ctx.Controller):
        w.write_line(
            f"func (ctrl *{self._struct_name(ctrl)}) Routes() []httpapi.Route {{",
        ).push_indent()
        w.write_line(
            "return [] httpapi.Route {",
        ).push_indent()
        for r in ctrl.routes:
            w.write_line(
                f'{{ Path: "{r.url}\", Method: \"{r.method}\", Name: "{r.operation_name}", Handler: ctrl.{r.operation_name}}},',
            )
        w.pop_indent()
        w.write_line(
            "}",
        ).pop_indent()
        w.write_line(
            "}",
            ""
        )
        pass

    def _write_methods(self, w: Writer, ctrl: ctx.Controller):
        for route in ctrl.routes:
            self._write_method(w, ctrl, route)
    
    def _write_method(self, w: Writer, ctrl: ctx.Controller, route: ctx.ControllerRoute):
        w.write_line("/*")
        w.write_line(f"{route.operation_name}: {route.method} {route.url}")
        w.write_line("Description: " + route.description)
        w.write_line("*/")
        w.write_line(
            f"func (ctrl *{self._struct_name(ctrl)}) {route.operation_name}(w http.ResponseWriter, r *http.Request) {{",
        )
        w.push_indent()
        request_body: Component = route.requestBody()
        if request_body != None:
            modelname = request_body.model_name
            full_modelname = request_body.full_model_name
            new_modelname = f"{self._ctx.models_prefix}New{modelname}"

            w.write_line(
                f"var item {full_modelname}",
                "if r.Body != nil {",
                "   body, _ := ioutil.ReadAll(r.Body)",
                "    if body != nil {",
                f"        item = {new_modelname}()",
                "        err := item.FromJson(string(body))",
                "        if err != nil {",
                "            item = nil",
                "        }",
                "    }",
                "}",
                f"result := ctrl.handler.{route.operation_name}(item, r)",
            )
        else:
            w.write_line(
                f"result := ctrl.handler.{route.operation_name}(r)",
            )


        for response in route.responses:
            w.write_line(
                f"if result.HasStatusCode{response.response_value}() {{",
            ).push_indent()
            # print(response_obj)
            # no response content defined, return as 'any'
            write_method = None
            if response.has_json:
                write_method = "WriteJSONResponse"
            elif response.has_binary:
                write_method = "WriteByteResponse"
            else:
                write_method = "WriteAnyResponse"
            w.write_line(
                "httpapi.{write_method}(w, {response_value}, result.StatusCode{response_value}())".format(
                    write_method=write_method,
                    response_value=response.response_value
                )
            )
            w.write_line("return")
            w.pop_indent()
            w.write_line(
                "}",
            )

        # w.push_indent()
        # for r in ctrl.routes:
        #     w.write_line(
        #         f"httpapi.Route(\"{r.url}\", ctrl.{r.operation_name}, \"{r.method}\"),",
        #     )
        # w.pop_indent()
        w.write_line("httpapi.WriteDefaultResponse(w, http.StatusInternalServerError)")
        w.pop_indent()
        w.write_line(
            "}",
            ""
        )
        pass


    # def _write_servicehandler_interface(self, w: Writer, ctrl: ctx.Controller):
    #     w.write_line(
    #         f"type {ctrl.service_handler_name} interface {{",
    #     )
    #     w.push_indent()
    #     w.write_line(
    #         f"GetController() {ctrl.controller_name}",
    #     )
    #     for r in ctrl.routes:
    #         response_model_name = r.operation_name + 'Response'
    #         w.write_line(
    #             f"{r.operation_name}(r *http.Request) models.{response_model_name}",
    #         )
    #     w.pop_indent()
    #     w.write_line(
    #         "}",
    #         ""
    #     )
    #     pass


