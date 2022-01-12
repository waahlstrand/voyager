export default {
    document: {
        title: 'Ocean Voyager'
    },
    api: {
        base: {
            url: 'https://voyager.gu.se/api/',
        },
        trajectory: {
            url: 'trajectory/'
        },
        vessels: {
            url: 'vessels/'
        }
    },
    data: '',
    tip: '🖱️ Right click on the map to add start points and a destination for your vessels!',
    icons: {
        pin: "https://img.icons8.com/small/50/000000/sailing-ship-small.png",
        target: "https://img.icons8.com/small/50/000000/finish-flag.png",
        clear: "https://img.icons8.com/material/50/000000/delete-forever--v1.png",
        zoom_in: "https://img.icons8.com/material/50/000000/plus-math--v2.png",
        zoom_out: "https://img.icons8.com/material/50/000000/minus--v2.png"
    },
    header: {
        title: "Ocean Voyager ⛵",
        subtitle: "Exploration of seafaring",
        blurb: `The Ocean Voyager is an agent-based simulation system capable generating
        seafaring trajectories based on winds and sea currents. Developed
        at the Centre for Digital Humanities at the University of
        Gothenburg.`,
    },

    instructions: {
        title: `Usage and Instructions`,
        subtitlePurpose: `Purpose`,
        textPurpose: `The <i>Ocean Voyager</i> is a demonstration of the underlying Voyager tool, meant to simulate trajectories 
        for ocean vessels with certain environmental conditions. Given a set of parameters and departure, the Voyager tool fetches data
        on the ocean current and winds and tries to calculate routes. It can be used to specify a set of departure points and a destination
        to approximate possible courses to reach the target.`,
        subtitleInstructions: `Instructions`,
        steps: [
            {
                id: 1,
                image: '/assets/images/departure.png',
                text: `First choose a starting position for your vessels. Right-click on the map and select <i>Add a departure point</i>. 
                        A small boat icon will appear on the coordinates. You can add multiple departure points by repeating this procedure.`
            },
            {
                id: 2,
                image: '/assets/images/destination.png',
                text: `Next choose a single destination for your vessels. Right-click on the map and select <i>Add a destination point</i>. 
                        A small flag icon will appear on the coordinates. You may only have a single destination for your vessels.`
            },
            {
                id: 3,
                image: '/assets/images/settings.png',
                text: `Now choose settings in the left sidebar. 
                        <ul>
                            <li><b>Dates</b>: Select a range of dates from which to load the data and run the simulation.</li>
                            <li><b>Propulsion type</b>: Select how the boats move; with sailing, paddling, or drifting without a destination.</li>
                            <li><b>Vessel type</b>: Select a type of vessel with the chosen mode of propulsion.</li>
                            <li><b>Paddling speed</b>: If the boats are paddling, enter a mean speed.</li>
                        </ul>
                        Observe that for sailing and paddling, a destination point is required, but not when drifting. When drifting, the destination will be
                        ignored, and the vessel will follow the winds and currents.`
            },
            {
                id: 4,
                image: '/assets/images/successful.png',
                text: `Finally click <i>Run</i> in the left sidebar. A loading screen will appear, and Voyager will simulate trajectories for your 
                        vessels`
            },
            {
                id: 5,
                image: '/assets/images/advanced.png',
                text: `For more control over the simulation, click the <i>Advanced</i> tab on the settings. Here you can specify
                    the following parameters:
                    <ul>
                            <li><b>Launch interval</b>: The interval in days to send new boats, e.g. every 3 days.</li>
                            <li><b>Max journey length</b>: Enter a time limit in days for the simulated trajectories. </li>
                            <li><b>Timestep</b>: Control the resolution of the movement of the boats - a smaller value will simulate more fined-grained
                            movements, but also take more time to calculate. Larger timesteps result in quicker simulations, but larger 'jumps' for the vessel.</li>
                    </ul>
                    In general, smaller geographical regions require a smaller timestep, and larger geographical regions (e.g. the Atlantic Ocean), 
                    are more suitable for longer timesteps.
                    `
            }   
        ]
    },
    about: {
        title: `About Voyager`,
        text: `Ocean Voyager simulates sea routes on a global scale, during different seasons 
        and phases in history and prehistory. The tool will provide novel approaches to analysing 
        and validating ancient trade routes, migration and cultural exchange. <br><br>

        Voyager utilizes experimental data on prehistoric boats with different capacity 
        (e.g. log boats, plank-built boats, bark boats, skin boats) and various modes of propulsion 
        as affected by meteorological and oceanographic patterns. <br><br>

        These patterns are based on open-source present-day data on sea currents and wind 
        collected by Copernicus (European Union's Earth Observation Programme) 
        and ECMWF (European Centre for Medium-Range Weather Forecasts). <br><br>

        The tool is currently a prototype but will be fully developed within the research programme 
        Maritime Encounters a counterpoint to the dominant terrestrial narrative of European prehistory 
        (funded by Riksbankens Jubileumsfond, 2022–2027), led by Professor Johan Ling Department of 
        Historical studies/SHFA, University of Gothenburg`
    },
    projection: {
        to: "EPSG:4326",
        from: "EPSG:3857",
        center: [3, 55],
        zoom: 6
    }
}