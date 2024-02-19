function setSwal(param1, data, status) {
    switch (status) {
        case 1:
            swal({title: param1, text: data, type: "success", timer: 9000});
            break;
        case 2:
            swal({title: param1, text: data, type: "error", timer: 9000});
            break;
        default:
            break;
    }
}

function _preloader(toState) {
    if (toState === 'hide') {
        $('#spinner').css({"display": "none"});
    } else if (toState === 'show') {
        $('#spinner').css({"display": "block"});
    }
}


function takeDatabaseBackupHome() {
    swal({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes'
    }).then((result) => {
        if (result.isConfirmed) {
            _preloader('show');
            $.ajax({
                url: "/api/take-backup/",
                method: 'GET',
                dataType: "json",
                success: function (data) {
                    swal({title: "Success!", text: 'Backup done successfully!', type: "success", timer: 9000});
                    _preloader('hide');
                },
                error: function (data) {
                    _preloader('hide');
                    swal({title: "Error!", text: 'Something went wrong!', type: "error", timer: 9000});
                }
            });
        } else if (result.isDenied) {
            swal({title: "Cancelled!", text: 'Cancelled!', type: "info", timer: 9000});
        }
    });
}

function restoreDatabaseBackupHome() {
    var backup_date = document.getElementById("branch_select").value
    swal({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes'
    }).then(function (result) {
        _preloader('show');
        $.ajax({
            url: "/api/restore/",
            method: 'POST',
            dataType: "json",
            data: {"backup_date": backup_date},
            success: function (data) {
                swal({title: "Success!", text: 'Backup restored Successfully!', type: "success", timer: 9000});
                _preloader('hide');
            },
            error: function (data) {
                _preloader('hide');
                swal({title: "Error!", text: data["responseJSON"]["message"], type: "error", timer: 9000});
            }
        });
    });
}

function printError(elementId, hintMessage) {
    document.getElementById(elementId).innerHTML = hintMessage;
}

function getDbCollections() {
    var dbname = $("#select-database").val();
    if (dbname !== null) {
        params = "?dbname=" + dbname;
        window.location.replace("/cleanup" + params);
    } else {
        window.location.replace("/cleanup");
    }
}

function validateFields() {
    var database = $("#database").val();
    var collection = $("#collection").val();
    var validated_data = {
        "validated": true,
        "database": database,
        "collection": collection,
    }

    // Validate database name
    if (database === "") {
        printError("database-error", "Please enter a valid database name");
        validated_data["validated"] = false;
    }

    // Validate collection name
    if (collection === "") {
        printError("collection-error", "Please enter a valid collection name");
        validated_data["validated"] = false;
    }
    return validated_data
}

function validateDeleteDBFields() {
    let database = $("#database-del-input").val();
    let validated_data = {
        "validated": true,
        "database": database,
    }

    // Validate database name
    if (database === "") {
        printError("database-error", "Please enter a valid database name");
        validated_data["validated"] = false;
    }

    return validated_data
}

function deleteCollection() {
    var validated_data = validateFields()

    if (validated_data["validated"] === true) {
        callDeleteCollectionApi(validated_data["database"], validated_data["collection"])
    } else {
        swal({title: "Error!", text: 'You need to select database and collection!', type: "error", timer: 9000});
    }
}

function deleteDatabase() {
    var validated_data = validateDeleteDBFields()

    if (validated_data["validated"] === true) {
        callDeleteDatabaseApi(validated_data["database"])
    } else {
        swal({title: "Error!", text: 'You need to select a database!', type: "error", timer: 9000});
    }
}

function callDeleteCollectionApi(database, collection) {
    swal({
        title: 'Are you sure to delete this collection?',
        text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes'
    }).then(function (result) {
        _preloader('show');
        $.ajax({
            url: "/api/delete_collection/",
            method: 'POST',
            dataType: "json",
            data: {
                "database": database,
                "collection": collection,
            },
            success: function (data) {
                $("#database").val("");
                swal({title: "Success!", text: 'Collection Deleted Successfully!', type: "success", timer: 9000});
                _preloader('hide');
                getDbCollections();
            },
            error: function (data) {
                _preloader('hide');
                swal({title: "Error!", text: data["responseJSON"]["message"], type: "error", timer: 9000});
            }
        });
    });
}


function callDeleteDatabaseApi(database) {
    swal({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes'
    }).then(function (result) {
        _preloader('show');
        $.ajax({
            url: "/api/delete_database/",
            method: 'POST',
            dataType: "json",
            data: {
                "database": database,
            },
            success: function (data) {
                $("#database-del-input").val("");
                $("#collection").val("");
                swal({title: "Success!", text: 'Database Deleted Successfully!', type: "success", timer: 9000});
                _preloader('hide');
            },
            error: function (data) {
                _preloader('hide');
                swal({title: "Error!", text: data["responseJSON"]["message"], type: "error", timer: 9000});
            }
        });
    });
}

function dropDown(event) {
    event.target.parentElement.children[1].classList.remove("d-none");
    $("#overlay").removeClass("d-none");
}


function getCollectionsBackup(token) {
    const databases = $("#select-databases").val();
    if (databases === null) {
        return;
    }
    _preloader('show');
    $.ajax({
        url: '/api/get-collection/',
        method: 'POST',
        headers: {'X-CSRFToken': token},
        data: JSON.stringify({"databases": databases}),
        contentType: 'application/json',
        success: function (data) {
            const collectionsData = data.collections_data;
            let collectionsMenu = $('#select-collections');
            // empty collection menu
            collectionsMenu.empty();
            $.each(collectionsData, function (key, value) {
                let optgroup = `
                    <optgroup label="${key}">
                        ${value.map(v => `<option value="${v}">${v}</option>`).join('')};
                    </optgroup>
                `
                collectionsMenu.append(optgroup);
            });
            collectionsMenu.trigger('change');
            _preloader('hide');
        },
        error: function (error) {
            console.log(error);
            _preloader('hide');
        }
    });
}


function getCollectionsDataView(token, database) {
    if (database === null) {
        return;
    }
    _preloader('show');
    $.ajax({
        url: '/api/get-collection/',
        method: 'POST',
        headers: {'X-CSRFToken': token},
        data: JSON.stringify({"databases": [database]}),
        contentType: 'application/json',
        success: function (data) {
            const collectionsData = data.collections_data;
            let collectionsMenu = $('#select-collections');
            // empty collection menu
            collectionsMenu.empty();
            $.each(collectionsData, function (key, value) {
                let optgroup = `
                    <optgroup label="${key}">
                        ${value.map(v => `<option value="${v}">${v}</option>`).join('')};
                    </optgroup>
                `
                collectionsMenu.append(optgroup);
            });
            collectionsMenu.trigger('change');
            _preloader('hide');
        },
        error: function (error) {
            console.log(error);
            _preloader('hide');
        }
    });
}

function databaseCheckboxLogic() {
    $('#database-option-all').click(function () {
        $('input[name="database-option"]').prop('checked', this.checked);
    });

    $('#database-option').click(function () {
        if ($('input[name="database-option"]').is(':checked')) {
            $('input[name="database-option-all"]').prop('checked', false);
        }
    })
}


function showToast(type, title) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: type,
        title: title,
        showConfirmButton: false,
        timer: 3000
    })
}


function takeDatabaseBackupPage(token) {
    const databases = $('#select-databases').val();
    const collections = $('#select-collections').val();

    if (databases === null || collections === null) {
        swal({title: "Error!", text: 'You need to select at least one collection!', type: "error", timer: 9000});
    } else {
        swal({
            title: 'Are you sure?',
            text: "This will take backup of the selected databases and collections!",
            type: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes'
        }).then((result) => {
            if (result.value) {
                _preloader('show');
                $.ajax({
                    url: "/api/take-backup_with_params/",
                    method: 'POST',
                    headers: {'X-CSRFToken': token},
                    dataType: "json",
                    data: JSON.stringify({"databases": databases, "collections": collections}),
                    contentType: 'application/json',
                    success: function (data) {
                        swal({title: "Success!", text: 'Backup done successfully!', type: "success", timer: 9000});
                        _preloader('hide');
                    },
                    error: function (data) {
                        _preloader('hide');
                        swal({title: "Error!", text: 'Something went wrong!', type: "error", timer: 9000});
                    }
                });
            }
        });
    }
}


function authenticateUser(token, username, password) {
    $.ajax({
        url: "/api/authenticate-user/",
        method: 'POST',
        headers: {'X-CSRFToken': token},
        dataType: "json",
        data: JSON.stringify({"username": username, "password": password}),
        contentType: 'application/json',
        success: function (data) {
            swal({title: "Success!", text: 'Authenticated Successfully!', type: "success", timer: 9000});
            _preloader('hide');
            $("#delete-btn").prop('disabled', false);
        },
        error: function (data) {
            console.log(data)
            _preloader('hide');
            swal({title: "Error!", text: 'Not Authenticated!', type: "error", timer: 9000});
        }
    });
}

function authenticateUserDatabase(token, username, password) {
    $.ajax({
        url: "/api/authenticate-user/",
        method: 'POST',
        headers: {'X-CSRFToken': token},
        dataType: "json",
        data: JSON.stringify({"username": username, "password": password}),
        contentType: 'application/json',
        success: function (data) {
            swal({title: "Success!", text: 'Authenticated Successfully!', type: "success", timer: 9000});
            _preloader('hide');
            $("#delete-database-btn").prop('disabled', false);
        },
        error: function (data) {
            console.log(data)
            _preloader('hide');
            swal({title: "Error!", text: 'Not Authenticated!', type: "error", timer: 9000});
        }
    });
}

function authenticateCollectionUser(token, username, password) {
    $.ajax({
        url: "/api/authenticate-user/",
        method: 'POST',
        headers: {'X-CSRFToken': token},
        dataType: "json",
        data: JSON.stringify({"username": username, "password": password}),
        contentType: 'application/json',
        success: function (data) {
            var database = $("#_database").text();
            var collection = $("#_collection").text();
            $("#AuthenticationModal").modal('hide');
            callDeleteCollectionApi(database, collection)
        },
        error: function (data) {
            _preloader('hide');
            swal({title: "Error!", text: 'Not Authenticated!', type: "error", timer: 9000});
        }
    });
}


// ----------------------------- Backup by using Cronjob ---------------------------------

function callCronjobApi(token, functionValue, cronTypeValue, timeValue) {
    swal({
        title: "Are you sure to perform this action?",
        text: `This will initiate cronjob at ${timeValue} ${cronTypeValue}`,
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes'
    }).then((result) => {
        if (result.value) {
            _preloader('show');
            $.ajax({
                url: `/api/initiate_cron/?function=${functionValue}`,
                headers: {'X-CSRFToken': token},
                method: 'POST',
                dataType: "json",
                data: JSON.stringify({
                    "cron_type": cronTypeValue,
                    "time": timeValue,
                }),
                contentType: 'application/json',
                success: function (data) {
                    $("#timepicker").val("");
                    $("#select-function").val("");
                    $("#cron-type").val("");
                    swal({title: "Success!", text: 'Cronjob created Successfully!', type: "success", timer: 9000});
                    _preloader('hide');
                },
                error: function (data) {
                    _preloader('hide');
                    swal({
                        title: "Error!",
                        text: data["responseJSON"]["detail"] || ["responseJSON"]["message"],
                        type: "error",
                        timer: 9000
                    });
                }
            });
        }
    });
}

// --------------------------- EXPORT CLUSTER --------------------------------------
function exportClusterApi() {
    swal({
        title: 'Ready?',
        text: "This will export all databases and their collections in cluster!",
        type: 'info',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes'
    }).then(function (result) {
        _preloader('show');
        fetch('/api/export_cluster/')
            .then(response => response.blob())
            .then(blobData => {
                const url = URL.createObjectURL(blobData);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'exported_data.xlsx';
                link.click();
                URL.revokeObjectURL(url);
                _preloader('hide');
                $('#export-btn').prop('disabled', false);
                swal({title: "Success!", text: 'Cluster Exported Successfully!', type: "success", timer: 9000});
            })
            .catch(error => {
                _preloader('hide');
                swal({title: "Error!", text: error, type: "error", timer: 9000});
                $('#export-btn').prop('disabled', false);
            });
    });
}

// --------------------------- Load mongocollections --------------------------------------
function loadMongoCollection(page, perPage,db_name, collection, sort, fil, token) {
    _preloader('show');
    $.ajax({
        method: "POST",
        headers: {'X-CSRFToken': token},
        url: "/api/load_mongo_collection/",
        data: JSON.stringify({
            "db_name": db_name,
            "collection": collection,
            "page": page,
            "per_page": perPage,
            "sort": sort,
            "filter": fil
        }),
        dataType: "json",
        contentType: 'application/json',
        success: function (data) {
            _preloader('hide');
            var start = ((data.page - 1) * data.per_page) + 1;
            var end = start + data.per_page - 1
            if (end > data.total) {
                end = data.total
            }
            if (start > data.total) {
                start = data.total
            }
            $('#total').html(data.total);
            $('#total1').html(data.total);

            $('#start').html(start);
            $('#start1').html(start);
            $('#start').attr('value', data.page);
            $('#start1').attr('value', data.page);


            $('#end').html(end);
            $('#end1').html(end);
            $('#per_page').html(data.per_page);
            $("#json").JSONView(data.json_data, {collapsed: true, nl2br: true,});
        },
        error: function (data) {
            _preloader('hide');
            swal({
                title: "Error!",
                text: data["responseJSON"]["message"],
                type: "error",
                timer: 9000
            });
        }

    })
}

// --------------------------- dataview pagination --------------------------------------

function pagination_right1(token) {
    var pg = parseInt($("#start1").attr('value'));
    var tt = parseInt($("#total1").text());  
    var db = $("#database_name").text();
    var col = $("#collec_name").text();
    var sor = $("#sort_name").text();
    var p_pag = parseInt($("#per_page").text());
    var filter_name = $("#filter_name").text();

    pg = pg + 1;
    if (((pg - 1) * p_pag) <= tt) {
        loadMongoCollection(pg, p_pag,db, col, sor, filter_name, token);
    }
}

function pagination_left1(token) {
    var pg = parseInt($("#start1").attr('value'));
    var db = $("#database_name").text();
    var col = $("#collec_name").text();
    var sor = $("#sort_name").text();
    var p_pag = parseInt($("#per_page").text());
    var filter_name = $("#filter_name").text();

    pg = pg - 1;
    if (pg >= 1) {
        loadMongoCollection(pg, p_pag,db, col, sor, filter_name, token);
    }
}

function pagination_right(token) {
    var pg = parseInt($("#start").attr('value'));
    var tt = parseInt($("#total").text());
    var p_pag = parseInt($("#per_page").text());
    var db = $("#database_name").text();
    var col = $("#collec_name").text();
    var sor = $("#sort_name").text();
    var filter_name = $("#filter_name").text();

    pg = pg + 1;
    if (((pg - 1) * p_pag) <= tt) {
        loadMongoCollection(pg, p_pag, db, col, sor, filter_name, token);
    }
}

function pagination_left(token) {
    var pg = parseInt($("#start").attr('value'));
    var db = $("#database_name").text();
    var col = $("#collec_name").text();
    var sor = $("#sort_name").text();
    var p_pag = parseInt($("#per_page").text());
    var filter_name = $("#filter_name").text();

    pg = pg - 1;
    if (pg >= 1) {
        loadMongoCollection(pg, p_pag, db, col, sor, filter_name, token);
    }
}


