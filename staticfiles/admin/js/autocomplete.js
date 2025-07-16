'use strict';
{
    const RWF = django.jQuery;

    RWF.fn.djangoAdminSelect2 = function() {
        RWF.each(this, function(i, element) {
            RWF(element).select2({
                ajax: {
                    data: (params) => {
                        return {
                            term: params.term,
                            page: params.page,
                            app_label: element.dataset.appLabel,
                            model_name: element.dataset.modelName,
                            field_name: element.dataset.fieldName
                        };
                    }
                }
            });
        });
        return this;
    };

    RWF(function() {
        // Initialize all autocomplete widgets except the one in the template
        // form used when a new formset is added.
        RWF('.admin-autocomplete').not('[name*=__prefix__]').djangoAdminSelect2();
    });

    document.addEventListener('formset:added', (event) => {
        RWF(event.target).find('.admin-autocomplete').djangoAdminSelect2();
    });
}
