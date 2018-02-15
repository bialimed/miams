/***************************************************************
*  Copyright notice
*
*  (c) 2015 PF bioinformatique de Toulouse
*  All rights reserved
*
*  It is distributed under the terms of the GNU General Public
*  License as published by the Free Software Foundation; either
*  version 2 of the License, or (at your option) any later version.
*
*  The GNU General Public License can be found at
*  http://www.gnu.org/copyleft/gpl.html.
*
*  This script is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  This copyright notice MUST APPEAR in all copies of the script!
***************************************************************/

(function (JflowWfformRules, $) {
    var self = JflowWfformRules;

    /**
	 * Add the exclude tag to target parameters to exclude (to disable)
	 * @param excludes: target parameters to excludes
	 * @param exclude_by: source parameter causing the excludes
	 * @private
	 */
	var _add_excludes_by_tag = function(excludes, exclude_by) {
		for (var e in excludes) {
			var exclude = $("#" + excludes[e]);
			var orig = "";
			if (exclude.attr("exclude-by") && exclude.attr("exclude-by").length > 0) {
				orig = exclude.attr("exclude-by");
			}
			if (orig.indexOf(exclude_by + ";") == -1) //If not already here
				exclude.attr("exclude-by", orig + exclude_by + ";");
		}
	}

	/**
	 * Add the required by tag to target parameters to require
	 * @param requires: target parameters to require
	 * @param required_by: source parameter causing the requirement
	 * @private
	 */
	var _add_to_be_required_by_tag = function(requires, required_by) {
		for (var r in requires) {
			var require = $("#" + requires[r]);
			var orig = "";
			if (require.attr("to-be-required-by") && require.attr("to-be-required-by").length > 0) {
				orig = require.attr("to-be-required-by");
			}
			if (orig.indexOf(required_by + ";") == -1) //if not already here
				require.attr("to-be-required-by", orig + required_by + ";");
		}
	}

	/**
	 * Remove the exclude tags to target parameters to re-enable
	 * @param excludes: target parameters to excludes
	 * @param exclude_by: source parameter causing the excludes
	 * @private
	 */
	var _remove_excludes_by_tag = function(excludes, exclude_by) {
		for (var e in excludes) {
			var exclude = $("#" + excludes[e]);
			if (exclude.attr("exclude-by")) {
				exclude.attr("exclude-by", exclude.attr("exclude-by").replace(exclude_by + ";", ""));
			}
		}
	}

	/**
	 * Remove the to be required tags to target parameters to make them optional
	 * @param requires
	 * @param required_by
	 * @private
	 */
	var _remove_to_be_required_by_tag = function(requires, required_by) {
		for (var r in requires) {
			var require = $("#" + requires[r]);
			if (require.attr("to-be-required-by")) {
				require.attr("to-be-required-by", require.attr("to-be-required-by").replace(required_by + ";", ""));
			}
		}
	}

	/**
	 * When an exclude rule is deleted, check if the parameter has to stay disabled (true if excluded by another param)
	 * @param param: the parameter to check
	 * @returns {*|boolean}: true if the parameter has to stay disabled
	 * @private
	 */
	var _get_param_keep_exclude = function(param) {
		var object = $("#" + param);
		return object.attr("exclude-by") && object.attr("exclude-by").length > 0
	}

	var _get_param_keep_required = function(param) {
		var object = $("#" + param);
		return object.attr("to-be-required-by") && object.attr("to-be-required-by").length > 0
	}

	/**
	 * Disable a parameter in the form
	 * @param param
	 * @private
	 */
	var _disable_parameters = function(param) {
		param.prop("disabled", true);
		var input_group = param.closest(".input-group");
		if (input_group.length > 0) { //There is an input group
			input_group.find(".btn").prop("disabled", true);
		}

		//param.css("text-decoration", )
	}

	/**
	 * Enable a parameter in the form
	 * @param param
	 * @private
	 */
	var _enable_parameters = function(param) {
		param.prop("disabled", false);
		var input_group = param.closest(".input-group");
		if (input_group.length > 0) { //There is an input group
			input_group.find(".btn").prop("disabled", false);
		}
	}

	var _check_condition_raised = function(conditions_params, which) {
		var condition_raised = false;
		var all_raised = true;
		for (var param in conditions_params) {
			var obj_param
			if (param.indexOf(">") == -1)
				obj_param = $("#" + param);
			else {
				var param_parts = param.split(">")
				obj_param = $("#" + param_parts[0] + "___" + param_parts[1].replace("_", "-"));
			}
			var value;
			if (obj_param.length > 0) {
				value = obj_param.val();
				if (obj_param.is("input[type=checkbox]")) {
					value = obj_param.is(":checked") ? "True" : "False";
				}
			}
			else if (param.indexOf(">") > -1) {
				var data = $("#handsontable_" + param.split(">")[0]).handsontable("getData");
				var column_name = param.replace("_", "-").replace(">", "___")
				value = "";
				for (var i in data) {
					var line = data[i]
					if (line[column_name] != null && line[column_name] != "") {
						value = "*"
					}
				}
			}
			else if (which == "ALL") {
				all_raised = false;
				break;
			}
			if (value !== undefined) {
				var c_values = conditions_params[param].values;
				if ((conditions_params[param].equal && (c_values.indexOf("*") > -1 && value != "" || c_values.indexOf(value) > -1
						|| c_values.indexOf("None") > -1 && value == "")) ||
						(!conditions_params[param].equal && c_values.indexOf(value) == -1)) {
					if (which == "ANY") {
						condition_raised = true;
						break;
					}
				}
				else if (which == "ALL") {
					all_raised = false;
					break;
				}
			}
		}
		if (which == "ALL" && all_raised) {
			condition_raised = true;
		}

		return condition_raised
	}

	var _add_event = function(calling_function, params, $this) {
		for (var p in params) {
			var param = params[p];
			if (param.indexOf(">") == -1) {
				$("#" + param).on("change", function() {
					calling_function();
				});
			}
			else {
				var param_parts = param.split(">");
				var obj_param = $("#" + param_parts[0] + "___" + param_parts[1].replace("_", "-"));
				if (obj_param.length == 0) {
					$this.$element.off("change_" + param.replace("_", "-").replace(">", "___"))
						.on("change_" + param.replace("_", "-").replace(">", "___"), function (e, value) {
						calling_function();
					});
				}
				else {
					obj_param.off("change").on("change", function() {
						calling_function();
					});
				}
			}
		}
	}

    /**
	 * For given rule, associate the event to check it client_side
	 * @param parameter_name: name of the parameter containing the rule
	 * @param rule: the rule string
	 * @param parameter_type: type of the parameter (str, bool, inputfile__s10, ...)
	 * @private
	 */
	self.add_event_rule_to_parameter = function (parameter_name, rule, parameter_type, $this) {
		var ruleExclude = /Exclude=(.+)/;
		var ruleToBeRequired = /ToBeRequired=(.+)/;
		var ruleRequiredIf = /RequiredIf\?(ANY|ALL)\[(.+)\]/;
		var ruleDisabledIf = /DisabledIf\?(ANY|ALL)\[(.+)\]/;
		var match;

		/**
		 * Disable targets excludes if source parameter is filled, re-enable it else
		 * @param change_on: the source parameter JQuery object
		 * @param excludes: name of targets excludes parameters
		 * @private
		 */
		var __exclude_targets = function(change_on, excludes) {
			excludes.splice(excludes.indexOf(change_on.attr("id")), 1);
			var excludes_objects = $("#" + excludes.join(", #"));
			if ((parameter_type != "bool" && change_on.val().length > 0) ||
				(parameter_type == "bool" && change_on.is(":checked"))) {
				_disable_parameters(excludes_objects)
				_add_excludes_by_tag(excludes, change_on.attr("id"))
			}
			else {
				_remove_excludes_by_tag(excludes, change_on.attr("id"))
				for (var e in excludes) {
					var exclude = excludes[e];
					if (!_get_param_keep_exclude(exclude)) {
						_enable_parameters($("#" + exclude));
					}
				}
			}
		}

		/**
		 * Add the required rule to the form for given targets (according to change_on input parameter)
		 * @param change_on
		 * @param targets
		 * @private
		 */
		var __add_required_target = function(change_on, targets) {
			_add_to_be_required_by_tag(targets, change_on.attr("id"))
			for (var i in targets) {
				var target = targets[i];
				var t_obj = $("#" + target);
				var current_rules = t_obj.rules();

				if ("required" in current_rules && current_rules["required"] === true
					&& t_obj.attr("initial_requirement") === undefined) {
					t_obj.attr("initial_requirement", "TRUE");
				}
				else {
					t_obj.attr("initial_requirement", "FALSE");
				}
				t_obj.rules("add", {"required": true});
			}
		}

		/**
		 * Remove the required rule to the form for given targets (according to change_on input parameter)
		 * @param change_on
		 * @param targets
		 * @private
		 */
		var __remove_required_target = function(change_on, targets) {
			_remove_to_be_required_by_tag(targets, change_on.attr("id"))
			for (var i in targets) {
				var target = targets[i];
				var t_obj = $("#" + target);
				var current_rules = t_obj.rules();
				if ("required" in current_rules && current_rules["required"] === true) {
					if ((t_obj.attr("initial_requirement") === undefined || t_obj.attr("initial_requirement") == "FALSE")
						 && (!_get_param_keep_required(target))) {
						t_obj.rules("remove", "required");
						t_obj.valid();
					}
				}
			}
		}

		/**
		 * Add required target rule if parameter is filled, else remove it
		 * @param change_on: parameter to be filled
		 * @param targets: targets to mark required
		 * @private
		 */
		var __required_targets = function(change_on, targets) {
			if (change_on.length > 0) {
				if ((parameter_type != "bool" && change_on.val().length > 0) ||
						(parameter_type == "bool" && change_on.is(":checked"))) {
					__add_required_target(change_on, targets);
				}
				else {
					__remove_required_target(change_on, targets);
				}
			}
			else {
				console.warn("Unable to change required option for parameter: " + target)
			}
		}

		var __check_disabled = function() {

			var condition_raised = _check_condition_raised(conditions_params, which);

            if (condition_raised) {
                param_input.closest("div.form-group").addClass("hidden-exclude").hide();
                param_input.addClass("hidden-exclude");
            }
            else {
				param_input.closest("div.form-group").removeClass("hidden-exclude").show();
                param_input.removeClass("hidden-exclude");
            }
            if (param_input.closest("fieldset").find(".param-field").not(".hidden-exclude").length == 0) {
                param_input.closest("fieldset").hide();
            }
            else {
                param_input.closest("fieldset").show();
            }
		}

		var __check_required = function() {
			var condition_raised = _check_condition_raised(conditions_params, which);

			var param_name = param_input.selector.substr(1);
			if (condition_raised) {
				if (param_name.indexOf("___") == -1) {
					param_input.rules("add", {"required": true});
				}
				else {
					handsontables[param_name.split("___")[0]].allRequired[param_name] = true;
				}
			}
			else {
				if (param_name.indexOf("___") == -1) {
                    param_input.rules("remove", "required");
                    param_input.valid();
                }
                else {
					handsontables[param_name.split("___")[0]].allRequired[param_name] = false;
					var nbRows = handsontables[param_name.split("___")[0]].handsontable("getData").length;
					for (var row = 0; row < nbRows; row++) {
						$this.handsontable_errors[param_name + "." + row] = undefined;
						$(handsontables["sample"].handsontable("getCell", row, handsontables[param_name.split("___")[0]].columns.indexOf(param_name)))
							.removeClass("htInvalid")
					}
                }
			}
		}

		var __get_conditions_params = function() {
			var conditions_params = {};
			var re_cond = /([\w>]+)(!)?=(.*)/;
			for (var c in conditions) {
				var condition = conditions[c];
				var match = null;
				if (match = condition.match(re_cond)) {
					var name = match[1] != "self" ? match[1] : parameter_name;
					if (!(name in conditions_params)) {
						conditions_params[name] = {};
						conditions_params[name]["equal"] = match[2] === undefined;
					}
					if (!("values" in conditions_params[name]))
						conditions_params[name]["values"] = []
					conditions_params[name]["values"].push(match[3]);
				}
			}
			return conditions_params;
		}

        var targets, param_input, which, conditions, conditions_params;
		//Check rule Exclude
		if (match = rule.match(ruleExclude)) {
			targets = match[1].split(",");
			targets.push(parameter_name);
			var targets_elems = "#" + targets.join(", #");
			$(targets_elems).on("change", function() {
				var excludes = targets.slice(0);
				__exclude_targets($(this), excludes);
			});

			for (var i in targets) {
				var target = targets[i];
                var t_obj = $("#" + target)
				if (t_obj.val().length > 0) {
					var excludes = targets.slice(0);
					__exclude_targets(t_obj, excludes);
				}
			}
		}

		//Check rule ToBeRequired
		else if (match = rule.match(ruleToBeRequired)) {
			targets = match[1].split(",");
			param_input = $("#" + parameter_name);
			param_input.on("change", function() {
				__required_targets(param_input, targets);
			})

			__required_targets(param_input, targets);
		}

		//Check rule DisabledIf
		else if (match = rule.match(ruleDisabledIf)) {
            which = match[1]
			conditions = match[2].split(",");
			conditions_params = __get_conditions_params();
			param_input = $("#" + parameter_name);
			_add_event(__check_disabled, Object.keys(conditions_params), $this);
			__check_disabled();
		}

		//Check rule RequiredIf
		else if (match = rule.match(ruleRequiredIf)) {
			which = match[1]
			conditions = match[2].split(",");
			conditions_params = __get_conditions_params();
			param_input = $("#" + parameter_name);
			_add_event(__check_required, Object.keys(conditions_params), $this);
			__check_required();
		}

	}

	/**
	 * Check rules of parameters
	 * @param parameters: list of parameters
	 * @private
	 */
	self.check_parameters_rules = function(parameters, $this) {
		var parameters_by_name = {}
		for (var i in parameters) {
			var parameter = parameters[i];
			parameters_by_name[parameter.name] = parameter
			var rules, r, rule;
			if (parameter.rules && parameter.rules !== null) {
				rules = parameter.rules.split(";")
				for (r in rules) {
					rule = rules[r];
					self.add_event_rule_to_parameter(parameter.name, rule, parameter.type, $this)
				}
			}
			if (parameter.type == "MultipleParameters" && parameter.sub_parameters) {
				for (var j in parameter.sub_parameters) {
					var sub_parameter = parameter.sub_parameters[j];
					if (sub_parameter.rules && sub_parameter.rules !== null) {
						rules = sub_parameter.rules.split(";");
						for (r in rules) {
							rule = rules[r];
							self.add_event_rule_to_parameter(sub_parameter.name, rule, sub_parameter.type, $this)
						}
					}
					parameters_by_name[sub_parameter.name] = sub_parameter
				}
			}
		}
		return parameters_by_name
	}

})(window.JflowWfformRules = window.JflowWfformRules || {}, jQuery)