/*global DateTimeShortcuts, SelectFilter*/
/**
 * Django admin inlines
 *
 * Based on jQuery Formset 1.1
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Spiced up with Code from Zain Memon's GSoC project 2009
 * and modified for Django by Jannis Leidel, Travis Swicegood and Julien Phalip.
 *
 * Licensed under the New BSD License
 * See: https://opensource.org/licenses/bsd-license.php
 */
'use strict';
{
    const RWF = django.jQuery;
    RWF.fn.formset = function(opts) {
        const options = RWF.extend({}, RWF.fn.formset.defaults, opts);
        const RWFthis = RWF(this);
        const RWFparent = RWFthis.parent();
        const updateElementIndex = function(el, prefix, ndx) {
            const id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
            const replacement = prefix + "-" + ndx;
            if (RWF(el).prop("for")) {
                RWF(el).prop("for", RWF(el).prop("for").replace(id_regex, replacement));
            }
            if (el.id) {
                el.id = el.id.replace(id_regex, replacement);
            }
            if (el.name) {
                el.name = el.name.replace(id_regex, replacement);
            }
        };
        const totalForms = RWF("#id_" + options.prefix + "-TOTAL_FORMS").prop("autocomplete", "off");
        let nextIndex = parseInt(totalForms.val(), 10);
        const maxForms = RWF("#id_" + options.prefix + "-MAX_NUM_FORMS").prop("autocomplete", "off");
        const minForms = RWF("#id_" + options.prefix + "-MIN_NUM_FORMS").prop("autocomplete", "off");
        let addButton;

        /**
         * The "Add another MyModel" button below the inline forms.
         */
        const addInlineAddButton = function() {
            if (addButton === null) {
                if (RWFthis.prop("tagName") === "TR") {
                    // If forms are laid out as table rows, insert the
                    // "add" button in a new table row:
                    const numCols = RWFthis.eq(-1).children().length;
                    RWFparent.append('<tr class="' + options.addCssClass + '"><td colspan="' + numCols + '"><a href="#">' + options.addText + "</a></tr>");
                    addButton = RWFparent.find("tr:last a");
                } else {
                    // Otherwise, insert it immediately after the last form:
                    RWFthis.filter(":last").after('<div class="' + options.addCssClass + '"><a href="#">' + options.addText + "</a></div>");
                    addButton = RWFthis.filter(":last").next().find("a");
                }
            }
            addButton.on('click', addInlineClickHandler);
        };

        const addInlineClickHandler = function(e) {
            e.preventDefault();
            const template = RWF("#" + options.prefix + "-empty");
            const row = template.clone(true);
            row.removeClass(options.emptyCssClass)
                .addClass(options.formCssClass)
                .attr("id", options.prefix + "-" + nextIndex);
            addInlineDeleteButton(row);
            row.find("*").each(function() {
                updateElementIndex(this, options.prefix, totalForms.val());
            });
            // Insert the new form when it has been fully edited.
            row.insertBefore(RWF(template));
            // Update number of total forms.
            RWF(totalForms).val(parseInt(totalForms.val(), 10) + 1);
            nextIndex += 1;
            // Hide the add button if there's a limit and it's been reached.
            if ((maxForms.val() !== '') && (maxForms.val() - totalForms.val()) <= 0) {
                addButton.parent().hide();
            }
            // Show the remove buttons if there are more than min_num.
            toggleDeleteButtonVisibility(row.closest('.inline-group'));

            // Pass the new form to the post-add callback, if provided.
            if (options.added) {
                options.added(row);
            }
            row.get(0).dispatchEvent(new CustomEvent("formset:added", {
                bubbles: true,
                detail: {
                    formsetName: options.prefix
                }
            }));
        };

        /**
         * The "X" button that is part of every unsaved inline.
         * (When saved, it is replaced with a "Delete" checkbox.)
         */
        const addInlineDeleteButton = function(row) {
            if (row.is("tr")) {
                // If the forms are laid out in table rows, insert
                // the remove button into the last table cell:
                row.children(":last").append('<div><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></div>");
            } else if (row.is("ul") || row.is("ol")) {
                // If they're laid out as an ordered/unordered list,
                // insert an <li> after the last list item:
                row.append('<li><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></li>");
            } else {
                // Otherwise, just insert the remove button as the
                // last child element of the form's container:
                row.children(":first").append('<span><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></span>");
            }
            // Add delete handler for each row.
            row.find("a." + options.deleteCssClass).on('click', inlineDeleteHandler.bind(this));
        };

        const inlineDeleteHandler = function(e1) {
            e1.preventDefault();
            const deleteButton = RWF(e1.target);
            const row = deleteButton.closest('.' + options.formCssClass);
            const inlineGroup = row.closest('.inline-group');
            // Remove the parent form containing this button,
            // and also remove the relevant row with non-field errors:
            const prevRow = row.prev();
            if (prevRow.length && prevRow.hasClass('row-form-errors')) {
                prevRow.remove();
            }
            row.remove();
            nextIndex -= 1;
            // Pass the deleted form to the post-delete callback, if provided.
            if (options.removed) {
                options.removed(row);
            }
            document.dispatchEvent(new CustomEvent("formset:removed", {
                detail: {
                    formsetName: options.prefix
                }
            }));
            // Update the TOTAL_FORMS form count.
            const forms = RWF("." + options.formCssClass);
            RWF("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);
            // Show add button again once below maximum number.
            if ((maxForms.val() === '') || (maxForms.val() - forms.length) > 0) {
                addButton.parent().show();
            }
            // Hide the remove buttons if at min_num.
            toggleDeleteButtonVisibility(inlineGroup);
            // Also, update names and ids for all remaining form controls so
            // they remain in sequence:
            let i, formCount;
            const updateElementCallback = function() {
                updateElementIndex(this, options.prefix, i);
            };
            for (i = 0, formCount = forms.length; i < formCount; i++) {
                updateElementIndex(RWF(forms).get(i), options.prefix, i);
                RWF(forms.get(i)).find("*").each(updateElementCallback);
            }
        };

        const toggleDeleteButtonVisibility = function(inlineGroup) {
            if ((minForms.val() !== '') && (minForms.val() - totalForms.val()) >= 0) {
                inlineGroup.find('.inline-deletelink').hide();
            } else {
                inlineGroup.find('.inline-deletelink').show();
            }
        };

        RWFthis.each(function(i) {
            RWF(this).not("." + options.emptyCssClass).addClass(options.formCssClass);
        });

        // Create the delete buttons for all unsaved inlines:
        RWFthis.filter('.' + options.formCssClass + ':not(.has_original):not(.' + options.emptyCssClass + ')').each(function() {
            addInlineDeleteButton(RWF(this));
        });
        toggleDeleteButtonVisibility(RWFthis);

        // Create the add button, initially hidden.
        addButton = options.addButton;
        addInlineAddButton();

        // Show the add button if allowed to add more items.
        // Note that max_num = None translates to a blank string.
        const showAddButton = maxForms.val() === '' || (maxForms.val() - totalForms.val()) > 0;
        if (RWFthis.length && showAddButton) {
            addButton.parent().show();
        } else {
            addButton.parent().hide();
        }

        return this;
    };

    /* Setup plugin defaults */
    RWF.fn.formset.defaults = {
        prefix: "form", // The form prefix for your django formset
        addText: "add another", // Text for the add link
        deleteText: "remove", // Text for the delete link
        addCssClass: "add-row", // CSS class applied to the add link
        deleteCssClass: "delete-row", // CSS class applied to the delete link
        emptyCssClass: "empty-row", // CSS class applied to the empty row
        formCssClass: "dynamic-form", // CSS class applied to each form in a formset
        added: null, // Function called each time a new form is added
        removed: null, // Function called each time a form is deleted
        addButton: null // Existing add button to use
    };


    // Tabular inlines ---------------------------------------------------------
    RWF.fn.tabularFormset = function(selector, options) {
        const RWFrows = RWF(this);

        const reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force
            if (typeof DateTimeShortcuts !== "undefined") {
                RWF(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        const updateSelectFilter = function() {
            // If any SelectFilter widgets are a part of the new form,
            // instantiate a new SelectFilter instance for it.
            if (typeof SelectFilter !== 'undefined') {
                RWF('.selectfilter').each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, false);
                });
                RWF('.selectfilterstacked').each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, true);
                });
            }
        };

        const initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                const field = RWF(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                RWF.each(dependency_list, function(i, field_name) {
                    dependencies.push('#' + row.find('.field-' + field_name).find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        RWFrows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
            },
            addButton: options.addButton
        });

        return RWFrows;
    };

    // Stacked inlines ---------------------------------------------------------
    RWF.fn.stackedFormset = function(selector, options) {
        const RWFrows = RWF(this);
        const updateInlineLabel = function(row) {
            RWF(selector).find(".inline_label").each(function(i) {
                const count = i + 1;
                RWF(this).html(RWF(this).html().replace(/(#\d+)/g, "#" + count));
            });
        };

        const reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force, yuck.
            if (typeof DateTimeShortcuts !== "undefined") {
                RWF(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        const updateSelectFilter = function() {
            // If any SelectFilter widgets were added, instantiate a new instance.
            if (typeof SelectFilter !== "undefined") {
                RWF(".selectfilter").each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, false);
                });
                RWF(".selectfilterstacked").each(function(index, value) {
                    SelectFilter.init(value.id, this.dataset.fieldName, true);
                });
            }
        };

        const initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                const field = RWF(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                RWF.each(dependency_list, function(i, field_name) {
                    // Dependency in a fieldset.
                    let field_element = row.find('.form-row .field-' + field_name);
                    // Dependency without a fieldset.
                    if (!field_element.length) {
                        field_element = row.find('.form-row.field-' + field_name);
                    }
                    dependencies.push('#' + field_element.find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        RWFrows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            removed: updateInlineLabel,
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
                updateInlineLabel(row);
            },
            addButton: options.addButton
        });

        return RWFrows;
    };

    RWF(document).ready(function() {
        RWF(".js-inline-admin-formset").each(function() {
            const data = RWF(this).data(),
                inlineOptions = data.inlineFormset;
            let selector;
            switch(data.inlineType) {
            case "stacked":
                selector = inlineOptions.name + "-group .inline-related";
                RWF(selector).stackedFormset(selector, inlineOptions.options);
                break;
            case "tabular":
                selector = inlineOptions.name + "-group .tabular.inline-related tbody:first > tr.form-row";
                RWF(selector).tabularFormset(selector, inlineOptions.options);
                break;
            }
        });
    });
}
