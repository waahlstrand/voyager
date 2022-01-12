export default {
    rules: {

        dates: [
            v => !!v || "Please specify a date range.",
            v => dateIsValid(v)
        ],

        propulsionTypes: [
            v => !!v || "Please choose a mode of propulsion."
        ],

        vesselTypes: [
            v => !!v || "Please choose a vessel type.",
        ],

        launchInterval: [
          (v) => !!v || "A launch interval is required.",
          (v) => (v && v > 0) || "Boats must be launched at least 1 day apart",
        ],
        journeyLength: [
            (v) => !!v || "A max journey length is required.",
            (v) => (v && v > 0) || "Must be a positive number."
        ],
        timestep: [
            (v) => !!v || "A simulation timestep is required.",
            (v) => (v && v > 0) || "Must be a positive number."
        ],
        paddlingSpeed: [
            (v) => !!v || "A mean speed is required when paddling.",
            (v) => (v && v > 0) || "Must be a positive number."
        ],
      }
}

function isSingleDate(d) {
    return Date.parse(d)

}

function dateRangeStr2dates(d) {

    d = d.split("~")

    return [new Date(d[0].trim()), new Date(d[1].trim())]

}

function dateRangeIsValid(dates) {

    const start = new Date('1993-1-1')
    const end = new Date('2018-12-31')
    
    return dates[0] > start && dates[1] < end; 


}

function dateRangeIsOrdered(dates) {

    return dates[1] > dates[0]


}

function dateIsValid(d) {

    if (d) {

        if (isSingleDate(d)) {
            return "Specify a range of dates."
        } else {
            const dates = dateRangeStr2dates(d)
            
            if (!dateRangeIsValid(dates)) {
                return "Date range must be between 1993 and 2018."
            } else if (!dateRangeIsOrdered(dates)) {
                return "End date must be later than the start date."
            } else {
                return true
            }
        }


    } else {
        return "Specify a range of dates."
    }

}