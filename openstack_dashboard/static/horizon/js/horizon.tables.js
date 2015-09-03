/* Namespace for core functionality related to DataTables. */
horizon.datatables = {
  timestamp_query: performance.now(),
  pending_request: undefined,
};

horizon.datatables.add_no_results_row = function (table) {
  /*// Add a "no results" row if there are no results.
  template = horizon.templates.compiled_templates["#empty_row_template"];
  if (!table.find("div.list-group-item:visible").length 
      && typeof(template) !== "undefined") {
    table.append(template.render());
  }*/
  table.find("p.empty").show();
};

horizon.datatables.remove_no_results_row = function (table) {
  table.find("p.empty").hide();
};

horizon.datatables.ajax_paginate = function(table, table_selector, page_num) {
  if (!table.attr('data-pagination-url')) {
    horizon.datatables.remove_no_results_row(table);
    return;
  }

  horizon.ajax.queue({
    type: 'GET',
    url: table.attr('data-pagination-url'),
    data: {
      page: page_num,
      application_id: table.attr('data-application_id'),
      organization_id: table.attr('data-organization_id'),
      name__startswith: table.find('div.table_search.client input').val() || undefined,
    },
    beforeSend: function () {
      // add a spinner to show progress
      var list_group = $('#'+table_selector).find('div.list-group');
      list_group.html('<i class="fa fa-gear fa-spin"></i>');
    },
    complete: function () {
    },
    error: function(jqXHR, status, errorThrown) {
    },
    success: function (data, textStatus, jqXHR) {
      var list_group = $('#'+table_selector).find('div.list-group');
      list_group.empty();

      // process data
      var items = data['items'];
      if (items.length) {
        horizon.datatables.remove_no_results_row(table);
      } else {
        horizon.datatables.add_no_results_row(table);
      }
      var template = horizon.templates.compiled_templates["#table_row_template"];
      for (var i in items) {
        list_group.append(template.render(items[i]));
      }

      // reinitialize pagination
      horizon.datatables.init_pagination(table, table_selector, data['pages']);
    }
  });
}
horizon.datatables.init_pagination = function (table, table_selector, total_pages) {
  if (total_pages <= 0) {
    // to force pagination clearing, we set page to 1
    total_pages = 1;
  }
  // init bootpag
  $('#'+table_selector+'_pagination_container').bootpag({
      total: total_pages,
      first: 'First',
      last:'Last',
      maxVisible: 10,
      wrapClass: 'pagination',
      firstLastUse: true
  }).on("page", function(event, page_num){ 
    horizon.datatables.ajax_paginate(table, table_selector, page_num);
  });
};

horizon.datatables.set_pagination_filter = function(table, table_selector) {
  var MIN_TIME_BETWEEN_QUERIES = 600; // ms
  var MIN_LETTERS_TO_QUERY = -1;

  table.find('div.table_search.client input').on('input', function() {
    var $input = $(this);
    var filter_data = $input.attr('value');
    if (filter_data.length < MIN_LETTERS_TO_QUERY){
      return;
    }

    var dif =  performance.now() - horizon.datatables.timestamp_query;
    if(dif < MIN_TIME_BETWEEN_QUERIES){
      if (horizon.datatables.pending_request !== undefined) {
        // kill previous request
        window.clearTimeout(horizon.datatables.pending_request);
      }
    }

    //store query time
    horizon.datatables.timestamp_query = performance.now();

    horizon.datatables.pending_request = window.setTimeout(function() {
        horizon.datatables.ajax_paginate(table, table_selector, 1);
      }, MIN_TIME_BETWEEN_QUERIES);
  });

};

horizon.datatables.set_table_query_filter = function (parent) {
  horizon.datatables.qs = {};
  $(parent).find('div.panel').each(function (index, elm) {
    var input = $($(elm).find('div.table_search.client input')),
        table_selector;
    if (input.length > 0) {
      // Disable server-side searching if we have client-side searching since
      // (for now) the client-side is actually superior. Server-side filtering
      // remains as a noscript fallback.
      // TODO(gabriel): figure out an overall strategy for making server-side
      // filtering the preferred functional method.
      input.on('keypress', function (evt) {
        if (evt.keyCode === 13) {
          return false;
        }
      });
      input.next('button.btn span.fa-search').on('click keypress', function (evt) {
        return false;
      });

      // Enable the client-side searching.
      table_selector = '#' + $(elm).find('div.list-group').attr('id');

      var qs = input.quicksearch(table_selector + ' div.list-group-item', {
        'delay': 300,
        'loader': 'span.loading',
        'bind': 'keyup click',
        'show': this.show,
        'hide': this.hide,
        onBefore: function () {
          var table = $(table_selector);
          horizon.datatables.remove_no_results_row(table);
        },
        onAfter: function () {
          var template, table, colspan, params;
          table = $(table_selector);
          horizon.datatables.add_no_results_row(table);
        },
        prepareQuery: function (val) {
          return new RegExp(val, "i");
        },
        testQuery: function (query, txt, _row) {
          return query.test($(_row).find('div.filter_field:not(.hidden):not(.actions_column)').text());
        }
      });
    }
  });
};


horizon.addInitFunction(function() {
  $('div.datatable').each(function (idx, el) {
    var table_selector = $(el).attr('id');

    // load intial elements
    horizon.datatables.ajax_paginate($(el), table_selector, 1);

    // set up filter
    horizon.datatables.set_pagination_filter($(el), table_selector)
  });

  // Trigger run-once setup scripts for tables.
  //horizon.datatables.set_table_query_filter($('body'));

  // Also apply on tables in modal views.
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_query_filter);

  // Also apply on tables in tabs views for lazy-loaded data.
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_query_filter);

});
