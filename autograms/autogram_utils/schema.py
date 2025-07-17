import ast
import copy

################################################################################
# Top-level transformer: finds `with apply_as_schema(...)` blocks
################################################################################

class ApplyAsSchemaTransformer(ast.NodeTransformer):
    """
    Scans the entire code for `with apply_as_schema(...)` blocks.
    When found, it transforms that block's statements using `SchemaBlockTransformer`.
    """

    def visit_With(self, node: ast.With):
        """
        If `with apply_as_schema(...): ...`, we apply our schema logic
        to node.body.
        """
        if self.is_apply_as_schema(node):
            # Create the schema block transformer
            schema_transformer = SchemaBlockTransformer()
            new_body = []
            for stmt in node.body:
                transformed = schema_transformer.visit(stmt)
                if isinstance(transformed, list):
                    new_body.extend(transformed)
                elif transformed:
                    new_body.append(transformed)

            # Option 1: Keep the `with` node but replace its body
            node.body = new_body
            # return node

            # Option 2: Remove the `with` statement entirely,
            # returning just the new_body as top-level statements
            # return new_body

            return node
        else:
            return self.generic_visit(node)

    def is_apply_as_schema(self, with_node: ast.With) -> bool:
        """
        Check if 'with apply_as_schema(...):'
        We'll do a quick check: the first with item is a call to 'apply_as_schema'.
        """
        if not with_node.items:
            return False
        expr = with_node.items[0].context_expr
        if isinstance(expr, ast.Call):
            # is the function name 'apply_as_schema'?
            if isinstance(expr.func, ast.Name):
                return expr.func.id == "apply_as_schema"
            elif isinstance(expr.func, ast.Attribute):
                return expr.func.attr == "apply_as_schema"
        return False


################################################################################
# SchemaBlockTransformer: transforms code inside an apply_as_schema block
################################################################################

class SchemaBlockTransformer(ast.NodeTransformer):
    """
    Rewrites loops & if-statements to produce a two-phase approach:
      - In _SCHEMA_BUILD_PHASE, we define sub-schemas
      - In the second pass, we read final JSON objects

    This is just a draft/skeleton. You can expand with real logic.
    """

    def __init__(self):
        super().__init__()
        self.loop_counter = 0
        self.if_counter = 0

    ############################################################################
    # Transform For-Loops
    ############################################################################

    def visit_For(self, node: ast.For):
        """
        Replace `for X in Y:` with something like:

          _auto_orig_list_<N> = Y
          _auto_index_<N> = 0
          while _auto_index_<N> < len(_auto_orig_list_<N>):
              X = _auto_orig_list_<N>[_auto_index_<N>]
              if _SCHEMA_BUILD_PHASE:
                  push_schema(parent_schema, 'loop_<N>_i')
              else:
                  sub_obj = parent_obj['loop_<N>_i']
                  push_obj(sub_obj)

              <transformed body>

              if _SCHEMA_BUILD_PHASE:
                  pop_schema()
              else:
                  pop_obj()

              _auto_index_<N> += 1
        """
        unique_id = self.loop_counter
        self.loop_counter += 1

        # Save the original node.iter for the array expression
        orig_iter = node.iter
        # We'll store it in a hidden var, e.g. "_auto_orig_list_<unique_id>"
        orig_list_var_name = f"_auto_orig_list_{unique_id}"
        orig_list_var = ast.Name(id=orig_list_var_name, ctx=ast.Store())

        # index var: "_auto_index_<unique_id>"
        index_var_name = f"_auto_index_{unique_id}"
        index_var_store = ast.Name(id=index_var_name, ctx=ast.Store())
        index_var_load = ast.Name(id=index_var_name, ctx=ast.Load())

        # 1) _auto_orig_list_<unique_id> = Y
        assign_list = ast.Assign(
            targets=[orig_list_var],
            value=orig_iter
        )

        # 2) _auto_index_<unique_id> = 0
        assign_index = ast.Assign(
            targets=[index_var_store],
            value=ast.Constant(value=0)
        )

        # Build the while condition: "_auto_index_<unique_id> < len(_auto_orig_list_<unique_id>)"
        while_condition = ast.Compare(
            left=index_var_load,
            ops=[ast.Lt()],
            comparators=[ast.Call(
                func=ast.Name(id="len", ctx=ast.Load()),
                args=[ast.Name(id=orig_list_var_name, ctx=ast.Load())],
                keywords=[]
            )]
        )

        # Build the while body
        while_body = []

        # item = _auto_orig_list_<unique_id>[_auto_index_<unique_id>]
        # (the 'target' of the for-loop is stored into the item)
        assign_item = ast.Assign(
            targets=[node.target],  # e.g. 'item'
            value=ast.Subscript(
                value=ast.Name(id=orig_list_var_name, ctx=ast.Load()),
                slice=index_var_load,
                ctx=ast.Load()
            )
        )
        while_body.append(assign_item)

        # Insert an if-check for build vs read
        push_block = self.build_push_schema_block(
            loop_name=f"loop_{unique_id}_",
            index_expr=index_var_load
        )
        while_body.extend(push_block)

        # Transform the loop body recursively
        transformed_body = []
        for stmt in node.body:
            out = self.visit(stmt)
            if isinstance(out, list):
                transformed_body.extend(out)
            elif out is not None:
                transformed_body.append(out)
        while_body.extend(transformed_body)

        # pop schema
        pop_block = self.build_pop_schema_block()
        while_body.extend(pop_block)

        # increment index
        increment = ast.AugAssign(
            target=ast.Name(id=index_var_name, ctx=ast.Store()),
            op=ast.Add(),
            value=ast.Constant(value=1)
        )
        while_body.append(increment)

        while_node = ast.While(
            test=while_condition,
            body=while_body,
            orelse=[]
        )

        return [assign_list, assign_index, while_node]

    def build_push_schema_block(self, loop_name, index_expr):
        """
        Returns a list of statements like:

            if _SCHEMA_BUILD_PHASE:
                push_schema(parent_schema, f"{loop_name}{i}")
            else:
                sub_obj = parent_obj[f"{loop_name}{i}"]
                push_obj(sub_obj)
        """
        # We'll build a f-string: loop_name + {index_expr}
        joined = ast.JoinedStr([
            ast.Constant(value=loop_name),
            ast.FormattedValue(value=index_expr, conversion=-1)
        ])

        # if node
        if_node = ast.If(
            test=ast.Name(id="_SCHEMA_BUILD_PHASE", ctx=ast.Load()),
            body=[
                # push_schema(parent_schema, joined)
                ast.Expr(value=ast.Call(
                    func=ast.Name(id="push_schema", ctx=ast.Load()),
                    args=[
                        ast.Name(id="parent_schema", ctx=ast.Load()),
                        joined
                    ],
                    keywords=[]
                ))
            ],
            orelse=[
                # sub_obj = parent_obj[joined]
                ast.Assign(
                    targets=[ast.Name(id="sub_obj", ctx=ast.Store())],
                    value=ast.Subscript(
                        value=ast.Name(id="parent_obj", ctx=ast.Load()),
                        slice=joined,
                        ctx=ast.Load()
                    )
                ),
                # push_obj(sub_obj)
                ast.Expr(value=ast.Call(
                    func=ast.Name(id="push_obj", ctx=ast.Load()),
                    args=[ast.Name(id="sub_obj", ctx=ast.Load())],
                    keywords=[]
                ))
            ]
        )

        return [if_node]

    def build_pop_schema_block(self):
        """
        if _SCHEMA_BUILD_PHASE:
            pop_schema()
        else:
            pop_obj()
        """
        return [ast.If(
            test=ast.Name(id="_SCHEMA_BUILD_PHASE", ctx=ast.Load()),
            body=[ast.Expr(value=ast.Call(
                func=ast.Name(id="pop_schema", ctx=ast.Load()),
                args=[],
                keywords=[]
            ))],
            orelse=[ast.Expr(value=ast.Call(
                func=ast.Name(id="pop_obj", ctx=ast.Load()),
                args=[],
                keywords=[]
            ))]
        )]

    ############################################################################
    # Transform If-Statements
    ############################################################################
    def visit_Assign(self, node: ast.Assign):
        """
        Suppose we see something like `x = StringField()`.
        We'll rewrite it into:

            if _SCHEMA_BUILD_PHASE:
                define_string(parent_schema, "x")
            else:
                x = parent_obj["x"]

        Then we copy the location info from the original `node` to the new `If`.
        """
        # 1) Check if it's a call to `StringField()`
        rhs = node.value
        if (isinstance(rhs, ast.Call)
            and isinstance(rhs.func, ast.Name)
            and rhs.func.id == "StringField"):
            
            # Suppose the target is a single variable
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                return node  # or raise an error if we only allow simple `var = ...`
            var_name = node.targets[0].id

            # 2) Build the "build" part
            build_expr = ast.Expr(value=ast.Call(
                func=ast.Name(id="define_string", ctx=ast.Load()),
                args=[
                    ast.Name(id="parent_schema", ctx=ast.Load()),
                    ast.Constant(value=var_name)
                ],
                keywords=[]
            ))
            # Copy location so this expression inherits the line numbers
            ast.copy_location(build_expr, node)

            # 3) Build the "read" part
            read_assign = ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=ast.Subscript(
                    value=ast.Name(id="parent_obj", ctx=ast.Load()),
                    slice=ast.Constant(value=var_name),
                    ctx=ast.Load()
                )
            )
            ast.copy_location(read_assign, node)

            # 4) Build an `if _SCHEMA_BUILD_PHASE: [build_expr] else: [read_assign]`
            if_node = ast.If(
                test=ast.Name(id="_SCHEMA_BUILD_PHASE", ctx=ast.Load()),
                body=[build_expr],
                orelse=[read_assign]
            )
            
            # 5) Copy the top-level location info from the original `Assign` node
            ast.copy_location(if_node, node)

            # 6) Possibly fix end_lineno, etc., or rely on fix_missing_locations.
            return if_node

        # If it's not `x = StringField()`, we just do normal recursion or leave it as-is
        return self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """
        We'll store each branch in a "decision" sub-schema for final JSON.
        Pseudocode:

        if _SCHEMA_BUILD_PHASE:
            # define branches for 'if'
        else:
            branch_chosen = parent_obj["decision_<id>"]

        # Actual runtime condition (the user's 'if node.test'):

        if node.test:
            # transform node.body
        else:
            # transform node.orelse

        This is just an example. You might also want to handle multiple elif, etc.
        """
        unique_id = self.if_counter
        self.if_counter += 1

        # 1) Build an 'if _SCHEMA_BUILD_PHASE:' snippet
        build_phase_body = [
            ast.Expr(value=ast.Call(
                func=ast.Name(id="push_decision_schema", ctx=ast.Load()),
                args=[
                    ast.Name(id="parent_schema", ctx=ast.Load()),
                    ast.Constant(value=f"decision_{unique_id}")
                ],
                keywords=[]
            ))
        ]
        read_phase_body = [
            # e.g. branch_chosen = parent_obj[f"decision_{unique_id}"]
            ast.Assign(
                targets=[ast.Name(id="branch_chosen", ctx=ast.Store())],
                value=ast.Subscript(
                    value=ast.Name(id="parent_obj", ctx=ast.Load()),
                    slice=ast.Constant(value=f"decision_{unique_id}"),
                    ctx=ast.Load()
                )
            )
        ]

        build_if = ast.If(
            test=ast.Name(id="_SCHEMA_BUILD_PHASE", ctx=ast.Load()),
            body=build_phase_body,
            orelse=read_phase_body
        )

        # 2) We'll transform node.body and node.orelse
        t_body = []
        for stmt in node.body:
            out = self.visit(stmt)
            if isinstance(out, list):
                t_body.extend(out)
            elif out is not None:
                t_body.append(out)

        t_orelse = []
        for stmt in node.orelse:
            out = self.visit(stmt)
            if isinstance(out, list):
                t_orelse.extend(out)
            elif out is not None:
                t_orelse.append(out)

        # 3) We'll create a new runtime if. Something like:
        # if node.test:
        #     <t_body>
        # else:
        #     <t_orelse>

        runtime_if = ast.If(
            test=node.test,
            body=t_body,
            orelse=t_orelse
        )

        return [build_if, runtime_if]

    ###########################################################################
    # Optionally handle other nodes (While, etc.) or raise errors for unsupported
    ###########################################################################

    def generic_visit(self, node):
        # For debugging, you could check node types. By default, do normal recursion
        return super().generic_visit(node)

import ast
import textwrap

import ast
import copy

class SimpleApplyAsSchemaTransformer(ast.NodeTransformer):
    """
    Transforms code of the form:
        with apply_as_schema(...) as parent_schema:
            VAR = RHS
            ...
    into:
        with apply_as_schema(...) as parent_schema:
            # Build block
            parent_schema.add_assign("VAR", <copied AST of RHS>)
            ...
            # generate object
            _auto_obj = generate_object(parent_schema.instruction, parent_schema.to_schema())
            # Read block
            VAR = _auto_obj["VAR"]
            ...
    """

    def visit_With(self, node: ast.With):
        # 1) Check if it's `with apply_as_schema(...) as something:`
        if not self.is_apply_as_schema(node):
            return self.generic_visit(node)

        as_var_name = self.extract_as_var(node.items[0])
        if not as_var_name:
            # No "as parent_schema"? skip or raise
            return self.generic_visit(node)

        # We'll gather "build" statements and "read" statements
        build_stmts = []
        read_stmts = []

        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                # e.g. `var = RHS`
                var_node = stmt.targets[0]
                if isinstance(var_node, ast.Name):
                    var_name = var_node.id
                    # The RHS is e.g. StringField()
                    # We want to pass that directly to parent_schema.add_assign(...)

                    # copy the RHS so we can place it in the new node
                    rhs_copy = copy.deepcopy(stmt.value)
                    # Build statement:
                    # parent_schema.add_assign("var_name", <rhs_copy>)
                    build_call = self.build_add_assign_call(
                        as_var_name, var_name, rhs_copy
                    )
                    ast.copy_location(build_call, stmt)
                    build_stmts.append(build_call)

                    # Read statement:
                    # var_name = _auto_obj["var_name"]
                    read_assign = ast.Assign(
                        targets=[ast.Name(id=var_name, ctx=ast.Store())],
                        value=ast.Subscript(
                            value=ast.Name(id="_auto_obj", ctx=ast.Load()),
                            slice=ast.Constant(value=var_name),
                            ctx=ast.Load()
                        )
                    )
                    ast.copy_location(read_assign, stmt)
                    read_stmts.append(read_assign)
                else:
                    # For complicated targets, we'll just keep it in build block
                    build_stmts.append(stmt)
            else:
                # For non-assign statements, we put them in build block (example logic)
                build_stmts.append(stmt)

        # Insert the _auto_obj = generate_object(...) line
        generate_obj_call = self.build_generate_object_call(as_var_name)
        # copy line info from last statement if possible
        if node.body:
            ast.copy_location(generate_obj_call, node.body[-1])
        else:
            ast.copy_location(generate_obj_call, node)

        all_new_body = build_stmts + [generate_obj_call] + read_stmts

        # Replace node.body with this new block
        node.body = all_new_body
        return node

    def is_apply_as_schema(self, with_node: ast.With) -> bool:
        if not with_node.items:
            return False
        expr = with_node.items[0].context_expr
        if isinstance(expr, ast.Call):
            # function name is apply_as_schema?
            if isinstance(expr.func, ast.Name):
                return expr.func.id == "apply_as_schema"
            elif isinstance(expr.func, ast.Attribute):
                return expr.func.attr == "apply_as_schema"
        return False

    def extract_as_var(self, with_item: ast.withitem):
        """
        with apply_as_schema(...) as parent_schema:
        -> returns "parent_schema"
        """
        if with_item.optional_vars and isinstance(with_item.optional_vars, ast.Name):
            return with_item.optional_vars.id
        return None

    def build_add_assign_call(self, parent_schema_name, var_name, rhs_expr):
        """
        Creates an ast.Expr node for:
          parent_schema_name.add_assign("var_name", RHS_Expr)
        """
        return ast.Expr(value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id=parent_schema_name, ctx=ast.Load()),
                attr="add_assign",
                ctx=ast.Load()
            ),
            args=[
                ast.Constant(value=var_name),  # e.g. "sentence"
                rhs_expr                       # e.g. StringField() copy
            ],
            keywords=[]
        ))

    def build_generate_object_call(self, parent_schema_name):
        """
        Creates `_auto_obj = generate_object(parent_schema.instruction, parent_schema.to_schema())`
        """
        return ast.Assign(
            targets=[ast.Name(id="_auto_obj", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="generate_object", ctx=ast.Load()),
                args=[
                    ast.Attribute(
                        value=ast.Name(id=parent_schema_name, ctx=ast.Load()),
                        attr="instruction",
                        ctx=ast.Load()
                    ),
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=parent_schema_name, ctx=ast.Load()),
                            attr="to_schema",
                            ctx=ast.Load()
                        ),
                        args=[],
                        keywords=[]
                    )
                ],
                keywords=[]
            )
        )
parent_schema.add_assign('instruction', 'write a sentence')
parent_schema.add_assign('sentence', StringField())
branch_point = parent_schema.add_branch_point('data',"Does the user want a conscise reply?")
branch_point.add_assign("instruction",'write a consise reply',branch="yes")
branch_point.add_assign("reply",StringField(),branch="yes")
branch_yes = branch_point.add_branch('yes')
branch_yes.add_assign("instruction",'write a consise reply')
branch_yes.add_assign('reply',StringField())
branch_no = branch_point.add_branch('no')
branch_no.add_assign(instruction,'write a verbose reply')
branch_no.add_assign('reply',StringField())




def test_function(users):
    with apply_as_schema() as parent_schema:
        instruction = "write a sentence"
        sentence=StringField()
        

        if 
    return "done"

if __name__=="__main__":
    CODE = """
def test_function(users):
    with apply_as_schema() as parent_schema:
        instruction = "write a sentence"
        sentence=StringField()
    return "done"
"""


def test_function(users):
    with apply_as_schema() as parent_schema:
        instruction = "write a sentence"
        sentence=StringField()
    return "done"
"""
    import ast

    module_ast = ast.parse(CODE)


    #apply_tr = ApplyAsSchemaTransformer()
    code_transformer = SimpleApplyAsSchemaTransformer()
    code_transformer.visit(module_ast.body[0])  # modifies in-place


    print(ast.unparse(module_ast))