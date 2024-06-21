
# Glossary of node fields

## Action

Type of action performed by node, also corresponds to node sub type


## Name
unique name of node

## other fields 


`transitions` -- list of allowable transitions

`notes` -- comments about what the node does

`state_category` -- user defined type of state. Names can be matched with `conv_scope` to view only states of that type when applying instruction

`transition_probs` --list of floats used for simulation probabilities of each possible transition

`instruction` -- instruction associated with node

`user_instruction_transitions` -- list of user instruction for when user simulates each transition. Should be same length as transitions

`question_prompt` -- prompt for transition question

`transition_question` -- question asked to determine which state to transition to.

`transition_choices` -- list of answers choices for transition question. If n'th transition choice is picked by model, autogram selects n'th transition. Should be same length as transitions

`user_interjection` -- user instruction when simulating interjection. Only interjection states use this. See predict_interjection() function

`condition_interjection` -- The answer to a multiple choice question used to predict an interjection. Only interjection states use this. See predict_interjection() function

`probability_interjection` -- The probability of simulating an interjection to this state during simulation. Only interjection states use this.

`example_interjection` -- Optional few shot example used to help predict interjection states.

`prerequisite_states` -- list of states used for special .* transitions, when choosing between possible transitions, heavily downweight if these states are not in stored states in memory object

`blocking_states` -- list of states used for special .* transitions, when choosing between possible transitions, heavily downweight if these states are in stored states in memory object

`up_weight_states` -- list of states used for special .* transitions, when choosing between possible transitions, slightly upweight if these states are in stored states in memory object

`down_weight_states` -- list of states used for special .* transitions, when choosing between possible transitions, slightly downweight if these states are in stored states in memory object. Can be used to penalize visiting the same state too often.

`boolean_condition` -- either variable or python statement that is evaluated as boolean, used for .* transitions. If True, select this node, otherwise go to next node in .* list

`required_revisit` -- list of states used to block function execution if states haven't been reached since last time function was called
`conv_scope` -- only view states corresponding to user defined state types in state category. If used, conv_scope should match the state_category of some of the nodes

`transition_context` --number of turns of context to use for transition prediction with classifier. Defaults to 1 if using default AutogramConfig

`instruction_template` --template for how instruction and last reply are displayed to model. Default is "<last_response>\n\nInstruction for <agent_name>: <instruction>" if using default AutogramConfig     