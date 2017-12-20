<script>
$(document).ready(function () {

    var updateFields = function(e, ui) {

        $td = ui.item.closest('td');

        var data = {};

        data[$td.data('x-field')] = $td.data('x-val');
        data[$td.data('y-field')] = $td.data('y-val');
        data.pk = ui.item.data('pk');
        console.log(data);

        $.ajax({
            url: "{{ url_for('update', table=selected_table) }}",
            method: "POST",
            traditional: true,
            data: data,
            error: function() {
                ui.sender.sortable("cancel");
            },
        });

    };

    $( ".sortable" ).sortable({
        connectWith: '.cell',
        revert: true,
        placeholder: "ui-state-highlight",
        forcePlaceholderSize: true,
        tolerance: "pointer",
        receive: updateFields,
        items: 'div.card'
    });

    $('#show_titles').change(function() {
        $('.title').slideToggle();
    });

    $('[name="show_fields"]').change(function() {
        var fieldName = $(this).attr('value');
        $('[data-field-name="'+fieldName+'"]').slideToggle();
    });


});
</script
