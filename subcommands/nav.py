from tradeenv import *

def navCommand(tdb, tdenv):
	"""
		Give player directions A->B
	"""

	srcSystem = tdenv.startSystem
	dstSystem = tdenv.stopSystem

	avoiding = []
	maxLyPer = tdenv.maxLyPer or tdb.maxSystemLinkLy

	tdenv.DEBUG(0, "Route from {} to {} with max {} ly per jump.",
					srcSystem.name(), dstSystem.name(), maxLyPer)

	openList = { srcSystem: 0.0 }
	distances = { srcSystem: [ 0.0, None ] }

	tdb.buildLinks()

	# As long as the open list is not empty, keep iterating.
	while openList and not dstSystem in distances:
		# Expand the search domain by one jump; grab the list of
		# nodes that are this many hops out and then clear the list.
		openNodes, openList = openList, {}

		for (node, startDist) in openNodes.items():
			for (destSys, destDist) in node.links.items():
				if destDist > maxLyPer:
					continue
				dist = startDist + destDist
				# If we already have a shorter path, do nothing
				try:
					distNode = distances[destSys]
					if distNode[0] <= dist:
						continue
					distNode[0], distNode[1] = dist, node
				except KeyError:
					distances[destSys] = [ dist, node ]
				assert not destSys in openList or openList[destSys] > dist
				openList[destSys] = dist

	# Unravel the route by tracing back the vias.
	route = [ dstSystem ]
	try:
		while route[-1] != srcSystem:
			jumpEnd = route[-1]
			jumpStart = distances[jumpEnd][1]
			route.append(jumpStart)
	except KeyError:
		print("No route found between {} and {} with {}ly jump limit.".format(srcSystem.name(), dstSystem.name(), maxLyPer))
		return
	route.reverse()
	titleFormat = "From {src} to {dst} with {mly}ly per jump limit."
	if tdenv.detail:
		labelFormat = "{act:<6} | {sys:<30} | {jly:<7} | {tly:<8}"
		stepFormat = "{act:<6} | {sys:<30} | {jly:>7.2f} | {tly:>8.2f}"
	elif not tdenv.quiet:
		labelFormat = "{sys:<30} ({jly:<7})"
		stepFormat  = "{sys:<30} ({jly:>7.2f})"
	elif tdenv.quiet == 1:
		titleFormat = "{src}->{dst} limit {mly}ly:"
		labelFormat = None
		stepFormat = " {sys}"
	else:
		titleFormat, labelFormat, stepFormat = None, None, "{sys}"

	if titleFormat:
		print(titleFormat.format(src=srcSystem.name(), dst=dstSystem.name(), mly=maxLyPer))

	if labelFormat:
		tdenv.printHeading(labelFormat.format(act='Action', sys='System', jly='Jump Ly', tly='Total Ly'))

	lastHop, totalLy = None, 0.00
	def present(action, system):
		nonlocal lastHop, totalLy
		jumpLy = system.links[lastHop] if lastHop else 0.00
		totalLy += jumpLy
		print(stepFormat.format(act=action, sys=system.name(), jly=jumpLy, tly=totalLy))
		lastHop = system

	present('Depart', srcSystem)
	for viaSys in route[1:-1]:
		present('Via', viaSys)
	present('Arrive', dstSystem)



subCommand_NAV = SubCommandParser(
	name='nav',
	cmdFunc=navCommand,
	help='Calculate a route between two systems.',
	arguments = [
		ParseArgument('startSys', help='System to start from', type=str),
		ParseArgument('endSys', help='System to end at', type=str),
	],
	switches = [
		ParseArgument('--ship',
				help='Use the maximum jump distance of the specified ship.',
				metavar='shiptype',
				type=str,
			),
		ParseArgument('--full',
				help='(With --ship) '
						'Limits the jump distance to that of a full ship.',
				action='store_true',
				default=False,
			),
		ParseArgument('--ly-per',
				help='Maximum light years per jump.',
				dest='maxLyPer',
				metavar='N.NN',
				type=float,
			),
	]
)
