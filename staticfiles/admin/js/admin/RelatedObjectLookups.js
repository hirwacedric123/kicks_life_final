/*global SelectBox, interpolate*/
// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
'use strict';
{
    const RWF = django.jQuery;
    let popupIndex = 0;
    const relatedWindows = [];

    function dismissChildPopups() {
        relatedWindows.forEach(function(win) {
            if(!win.closed) {
                win.dismissChildPopups();
                win.close();    
            }
        });
    }

    function setPopupIndex() {
        if(document.getElementsByName("_popup").length > 0) {
            const index = window.name.lastIndexOf("__") + 2;
            popupIndex = parseInt(window.name.substring(index));   
        } else {
            popupIndex = 0;
        }
    }

    function addPopupIndex(name) {
        return name + "__" + (popupIndex + 1);
    }

    function removePopupIndex(name) {
        return name.replace(new RegExp("__" + (popupIndex + 1) + "RWF"), '');
    }

    function showAdminPopup(triggeringLink, name_regexp, add_popup) {
        const name = addPopupIndex(triggeringLink.id.replace(name_regexp, ''));
        const href = new URL(triggeringLink.href);
        if (add_popup) {
            href.searchParams.set('_popup', 1);
        }
        const win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        relatedWindows.push(win);
        win.focus();
        return false;
    }

    function showRelatedObjectLookupPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^lookup_/, true);
    }

    function dismissRelatedLookupPopup(win, chosenId) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
            elem.value += ',' + chosenId;
        } else {
            document.getElementById(name).value = chosenId;
        }
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function showRelatedObjectPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
    }

    function updateRelatedObjectLinks(triggeringLink) {
        const RWFthis = RWF(triggeringLink);
        const siblings = RWFthis.nextAll('.view-related, .change-related, .delete-related');
        if (!siblings.length) {
            return;
        }
        const value = RWFthis.val();
        if (value) {
            siblings.each(function() {
                const elm = RWF(this);
                elm.attr('href', elm.attr('data-href-template').replace('__fk__', value));
                elm.removeAttr('aria-disabled');
            });
        } else {
            siblings.removeAttr('href');
            siblings.attr('aria-disabled', true);
        }
    }

    function updateRelatedSelectsOptions(currentSelect, win, objId, newRepr, newId) {
        // After create/edit a model from the options next to the current
        // select (+ or :pencil:) update ForeignKey PK of the rest of selects
        // in the page.

        const path = win.location.pathname;
        // Extract the model from the popup url '.../<model>/add/' or
        // '.../<model>/<id>/change/' depending the action (add or change).
        const modelName = path.split('/')[path.split('/').length - (objId ? 4 : 3)];
        // Select elements with a specific model reference and context of "available-source".
        const selectsRelated = document.querySelectorAll(`[data-model-ref="RWF{modelName}"] [data-context="available-source"]`);

        selectsRelated.forEach(function(select) {
            if (currentSelect === select) {
                return;
            }

            let option = select.querySelector(`option[value="RWF{objId}"]`);

            if (!option) {
                option = new Option(newRepr, newId);
                select.options.add(option);
                return;
            }

            option.textContent = newRepr;
            option.value = newId;
        });
    }

    function dismissAddRelatedObjectPopup(win, newId, newRepr) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem) {
            const elemName = elem.nodeName.toUpperCase();
            if (elemName === 'SELECT') {
                elem.options[elem.options.length] = new Option(newRepr, newId, true, true);
                updateRelatedSelectsOptions(elem, win, null, newRepr, newId);
            } else if (elemName === 'INPUT') {
                if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
                    elem.value += ',' + newId;
                } else {
                    elem.value = newId;
                }
            }
            // Trigger a change event to update related links if required.
            RWF(elem).trigger('change');
        } else {
            const toId = name + "_to";
            const o = new Option(newRepr, newId);
            SelectBox.add_to_cache(toId, o);
            SelectBox.redisplay(toId);
        }
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function dismissChangeRelatedObjectPopup(win, objId, newRepr, newId) {
        const id = removePopupIndex(win.name.replace(/^edit_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = RWF(selectsSelector);
        selects.find('option').each(function() {
            if (this.value === objId) {
                this.textContent = newRepr;
                this.value = newId;
            }
        }).trigger('change');
        updateRelatedSelectsOptions(selects[0], win, objId, newRepr, newId);
        selects.next().find('.select2-selection__rendered').each(function() {
            // The element can have a clear button as a child.
            // Use the lastChild to modify only the displayed value.
            this.lastChild.textContent = newRepr;
            this.title = newRepr;
        });
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function dismissDeleteRelatedObjectPopup(win, objId) {
        const id = removePopupIndex(win.name.replace(/^delete_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = RWF(selectsSelector);
        selects.find('option').each(function() {
            if (this.value === objId) {
                RWF(this).remove();
            }
        }).trigger('change');
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    window.showRelatedObjectLookupPopup = showRelatedObjectLookupPopup;
    window.dismissRelatedLookupPopup = dismissRelatedLookupPopup;
    window.showRelatedObjectPopup = showRelatedObjectPopup;
    window.updateRelatedObjectLinks = updateRelatedObjectLinks;
    window.dismissAddRelatedObjectPopup = dismissAddRelatedObjectPopup;
    window.dismissChangeRelatedObjectPopup = dismissChangeRelatedObjectPopup;
    window.dismissDeleteRelatedObjectPopup = dismissDeleteRelatedObjectPopup;
    window.dismissChildPopups = dismissChildPopups;

    // Kept for backward compatibility
    window.showAddAnotherPopup = showRelatedObjectPopup;
    window.dismissAddAnotherPopup = dismissAddRelatedObjectPopup;

    window.addEventListener('unload', function(evt) {
        window.dismissChildPopups();
    });

    RWF(document).ready(function() {
        setPopupIndex();
        RWF("a[data-popup-opener]").on('click', function(event) {
            event.preventDefault();
            opener.dismissRelatedLookupPopup(window, RWF(this).data("popup-opener"));
        });
        RWF('body').on('click', '.related-widget-wrapper-link[data-popup="yes"]', function(e) {
            e.preventDefault();
            if (this.href) {
                const event = RWF.Event('django:show-related', {href: this.href});
                RWF(this).trigger(event);
                if (!event.isDefaultPrevented()) {
                    showRelatedObjectPopup(this);
                }
            }
        });
        RWF('body').on('change', '.related-widget-wrapper select', function(e) {
            const event = RWF.Event('django:update-related');
            RWF(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                updateRelatedObjectLinks(this);
            }
        });
        RWF('.related-widget-wrapper select').trigger('change');
        RWF('body').on('click', '.related-lookup', function(e) {
            e.preventDefault();
            const event = RWF.Event('django:lookup-related');
            RWF(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                showRelatedObjectLookupPopup(this);
            }
        });
    });
}
