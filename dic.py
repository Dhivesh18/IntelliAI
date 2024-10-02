
def find_gop_using_ptf(user_query, gop_data):
    for gop, portfolios in gop_data[0].items():
        for i in range(len(portfolios)):
            return gop if portfolios[i]['Portfolio'] in user_query else "No Portfolio found"
        
gop_data = [
    {
        "DPS": [
            {"Portfolio": "PDS_ABC", "Status": "Active"},
            {"Portfolio": "PDS_XYZ", "Status": "Active"},
            {"Portfolio": "PDS_DEF", "Status": "Active"},
            {"Portfolio": "PDS_DEY", "Status": "Not Active"}
        ],
        "XYZ": [
            {"Portfolio": "XYZ_ABC", "Status": "Active"}
        ]
    }
]

print(find_gop_using_ptf("Portfolio is PDS_ABC",gop_data))

print(find_gop_using_ptf("Portfolio is SDF",gop_data))
               

