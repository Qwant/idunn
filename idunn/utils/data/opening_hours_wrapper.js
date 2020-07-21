// Wrapper around opening_hours.js API to ease interaction with Python. Wrapped
// functions globally behave the same with the following rules:
//
//   1. Input and output datetimes are iso formatted string and are independant
//      of the timezone.
//
//   2. Input opening hours are described by a raw string following the syntax
//   of the javascript implementation:
//   https://github.com/opening-hours/opening_hours.js#features

// Convert a naive ISO string into a locale date.
function fromNaiveIso(str) {
    const b = str.split(/\D/);
    return new Date(b[0], b[1]-1, b[2], b[3], b[4], b[5]);
}

// Convert a locale date into a naive ISO string and null if the date never
// changes.
function toNaiveIso(date) {
    if (!date) {
        return null;
    }

    const pad = function(num) {
        return (num < 10 ? '0' : '') + num;
    };

    return date.getFullYear() +
        '-' + pad(date.getMonth() + 1) +
        '-' + pad(date.getDate()) +
        'T' + pad(date.getHours()) +
        ':' + pad(date.getMinutes()) +
        ':' + pad(date.getSeconds())
}

// Check if an expression parses correctly and return an error description if
// not.
function validate(raw) {
    try {
        new opening_hours(raw, null);
        return true;
    }
    catch (err) {
        return "" + err;
    }
}

// Check if a given opening hours description is open at a given datetime.
function wrapIsOpen(raw, dt) {
    const oh = new opening_hours(raw, null);
    return oh.getState(fromNaiveIso(dt));
}

// Get next date of change for a given opening hours description starting at a
// given datetime.
function wrapNextChange(raw, dt) {
    const oh = new opening_hours(raw, null);
    return toNaiveIso(oh.getNextChange(fromNaiveIso(dt)));
}

// Get the list of open intervals for a given opening hours description between
// two given datetimes.
function wrapOpenIntervals(raw, from, to) {
    const oh = new opening_hours(raw, null);
    return oh.getOpenIntervals(fromNaiveIso(from), fromNaiveIso(to))
        .map(rg => [toNaiveIso(rg[0]), toNaiveIso(rg[1]), rg[2], rg[3]]);
}
