/**
 *
 * CC Network/sioc:has_owner Support
 * 
 */

YAHOO.cc.network.lookup_uri = function (metadata, network, work_uri) {
    // given a network URI, find the service URI that implements
    // the work lookup, if available

    // make sure we have metadata for this network
    if (!metadata[network]) return null;

    // see if any services are defined
    services = metadata[network]["http://rdfs.org/sioc/services#has_service"];
    if (services) {

	// see if any service implemented work-lookup
	for (var i = 0; i < services.length; i++) {
	    if (metadata[services[i]] &&
		metadata[services[i]]["http://rdfs.org/sioc/services#service_protocol"]) {
		// this service defines protocols, see if any match
		protocols = metadata[services[i]]["http://rdfs.org/sioc/services#service_protocol"];
		for (var j = 0; j < protocols.length; j++) {
		    if (protocols[j] == 
			"http://wiki.creativecommons.org/work-lookup") {

			// we have a match
			if (work_uri)
			    return services[i] + "?uri=" + work_uri;

			return services[i];
		    }
		} // for each protocol
		
	    } // if the service asserts protocols

	} // for each service

    } // if services were defined
	
    // no services, return null
    return null;

} // lookup_uri

YAHOO.cc.network.show_info = function(metadata, subject, owner) {

    // construct the text to insert
    owner_name = metadata[owner][SIOC('name')][0];
    network_url = metadata[owner][SIOC('member_of')][0];
    network_name = metadata[network_url][DCT('title')][0];

    lookup_uri = YAHOO.cc.network.lookup_uri(metadata, network_url, subject) || subject;

    var network_text = 	    
    '<a href="' + owner + '">' + owner_name + 
    '</a> has registered ' +
    '<a href="' + lookup_uri + '">this work</a> ' + 
    'at the <nobr><a href="' + network_url + '">' + 
    network_name + '</a></nobr>.';

    // create the new module to display the alert
    var module = new YAHOO.widget.Module("network", {visible:true});
    module.setBody(network_text);
    module.render(
		  YAHOO.util.Dom.getAncestorBy(
					       YAHOO.util.Dom.get("work-attribution-container"),
					       function(e) {return true;}));
    YAHOO.util.Dom.addClass(module.body, "network");

    module.show();
} // show_info

YAHOO.cc.network.match_iriset = function(metadata, iri_bnode, subject) {

    var r=0;

    // iterate over the inclusion regexes
    if (metadata[iri_bnode][POWDER("includeregex")])
    for (r = 0; 
	 r < metadata[iri_bnode][POWDER("includeregex")].length; 
	 r++){

	if (!(new RegExp(metadata[iri_bnode][POWDER("includeregex")][r])).
	    test(subject)) return false;
									   
    } // for each include regex


    // iterate over the exclusion regexes
    if (metadata[iri_bnode][POWDER("excluderegex")])
    for (r = 0; 
	 r < metadata[iri_bnode][POWDER("excluderegex")].length; 
	 r++){

	if ((new RegExp(metadata[iri_bnode][POWDER("excluderegex")][r])).
	    test(subject)) return false;
									   
    } // for each exclude regex

    return true;

} // match_iriset

YAHOO.cc.network.process_metadata = function (metadata, subject) {

    // see if this metadata contains an owner assertion
    if (metadata[subject][SIOC('has_owner')]) {
        // it does, see if there's a reciprocal ownership assertion
        owner_url = metadata[subject][SIOC('has_owner')][0];

        if (metadata[owner_url] &&
            metadata[owner_url][SIOC('owner_of')]) { 

            // they own *something* - check if it's the referer
            for (var o=0; o< metadata[owner_url][SIOC('owner_of')].length;o++){
		var owned_url = metadata[owner_url][SIOC('owner_of')][o];
		if (owned_url == subject) {

		    // Yay!
		    YAHOO.cc.network.show_info(metadata, owned_url,
					       owner_url);

		} // if ownership claims match
	    } // for each owned URL

	    // console.log(YAHOO.cc.license_uri(null));
            // no match yet; second pass to look for matching regexes
            for (var o=0; o< metadata[owner_url][SIOC('owner_of')].length;o++){
		var owned_url = metadata[owner_url][SIOC('owner_of')][o];

		// console.log('checking if ' + owned_url + ' contains the matching iriset');

		// console.log(YAHOO.cc.get_license(metadata, owned_url));
		// see if the owned URL has a license that matches us
		if (YAHOO.cc.get_license(metadata, owned_url) == YAHOO.cc.license_uri(null)) {
		    // console.log('license matches...');
		    // it has the same license; see if it's 
		    // parent has an iriset
		    if (metadata[owned_url][SIOC('has_parent')] &&
			metadata[metadata[owned_url][SIOC('has_parent')][0]][POWDER('iriset')]) {
			// console.log('it has a parent which has an iriset');
			// it has at least one IRI set, see if match...
			parent_url = metadata[owned_url][SIOC('has_parent')][0];
			for (var p=0; p<metadata[parent_url][POWDER('iriset')].length; p++) {
			    var iriset = metadata[parent_url][POWDER('iriset')][p];
			    if (YAHOO.cc.network.match_iriset(metadata,
							      iriset,
							      subject)) {
				YAHOO.cc.network.show_info(metadata, owned_url, owner_url);
			    } // if we match
			    
			} // for each iriset
		    } // if the parent has > 0 irisets
		} // if the work has the same license as we're viewing
	    } // for each owned work

	} // if ownership claims exist

    } // if a has_owner claim exists


} // add_details
