# Mikaela Dean, Spring 2022
# WSU CPTS315 HW 1
import time

# Global variables. Could be used as config params
IN_FILE = "../data/browsing-data.txt"
OUT_FILE = "./output.txt"
SUPPORT = 100

freq_items = {}


# File reading
def read_input():
	with open(IN_FILE, "r") as text_file:
		all_lines = text_file.readlines()

	return all_lines


# File dumping
def dump_output(pairs_confidence_list, triples_confidence_list):
	with open(OUT_FILE, "w") as text_file:
		text_file.write("OUTPUT A\n")
		for i in range(0, len(pairs_confidence_list)):
			text_file.write(str(pairs_confidence_list[i][1][0]) + " " + str(pairs_confidence_list[i][1][1]) + " " + "{:.4f}".format(pairs_confidence_list[i][0]) + "\n")
		text_file.write("OUTPUT B\n")
		for i in range(0, len(triples_confidence_list)):
			text_file.write(str(triples_confidence_list[i][1][0]) + " " + str(triples_confidence_list[i][1][1]) + " " + str(triples_confidence_list[i][1][2]) + " " + "{:.4f}".format(triples_confidence_list[i][0]) + "\n")
	text_file.close()
	return


# Returns c-length combos from line; ex: [1, 2, 3] -> [1, 2], [1, 3], [2, 3]
def get_combo(line, c):
	if c == 0:
		return [[]]
	combos = []
	for i in range(0, len(line)):
		start = line[i]
		rest = line[i + 1:]
		for ret in get_combo(rest, c - 1):
			combos.append([start] + ret)
	return combos


# Checks to see if every individual part of the combo is in the freq_list provided
def check_combo(combo, freq_list):
	if len(combo) != len(set(combo)):
		return False  # this means there's duplicates in the combo
	count = 0
	check_list = get_combo(combo, len(combo) - 1)
	for check in check_list:
		check = tuple(check)
		if check in freq_list:
			count += 1
	if count == len(combo):
		return True
	return False


# A-Priori Passes

# Pass 1: Read baskets and count in main memory the occurrences of each item
def pass_1(parsed_lines):
	singles_count_d = {}
	for basket in parsed_lines:
		for item in basket:
			singles_count_d[item] = singles_count_d.get(item, 0) + 1
	return singles_count_d


# Pass 2: Read baskets again and only count in main memory the pairs where both items are frequent
def pass_2(parsed_lines, n):
	pairs_count_a = [0 for i in range(int((n * (n - 1) / 2))+1)]
	for basket in parsed_lines:
		# remove not frequent items
		basket[:] = [item for item in basket if item in freq_items]
		# order in lowest to highest n-wise
		basket.sort(key=lambda x: freq_items[x])
		# get all i < j tuples of the current basket
		basket[:] = get_combo(basket, 2)
		# count all tuples
		for combo in basket:
			i = freq_items[combo[0]]
			j = freq_items[combo[1]]
			pairs_count_a[int((i - 1) * (n - i / 2) + j - i)] += 1
	return pairs_count_a


# Pass 3: Read buckets again and only count in main memory the triples where all pairs of the 3 items are frequent
def pass_3(parsed_lines, freq_pairs):
	triples_count_d = {}
	for basket in parsed_lines:
		# remove not frequent pairs
		basket[:] = [x for x in basket if tuple(x) in freq_pairs]
		used_starts = []
		for pair in basket:
			if pair[0] not in used_starts:
				# get all pairs in basket that start with the same number
				same_start = [x for x in basket if x[0] == pair[0]]
				if len(same_start) > 1:
					same_start = [x[1] for x in same_start]  # [1,2], [1,3], [1,4] -> [2, 3, 4]
					same_start = get_combo(same_start, 2)  # [2, 3, 4] -> [2,3], [2,4], [3,4]
					for potential in same_start:
						# if pair is frequent, then it is a frequent triple with the start number
						if tuple(potential) in freq_pairs:
							candidate = (pair[0], potential[0], potential[1])
							triples_count_d[candidate] = triples_count_d.get(candidate, 0) + 1
				used_starts.append(pair[0])
	return triples_count_d


# A-Priori Frequent Item Functions

# Finds and counts the number of all frequent items
def freq_item_count(singles_count_d):
	n = 0
	for item in singles_count_d:
		if singles_count_d[item] >= SUPPORT:
			n += 1
			freq_items[item] = n
	return n


# Calculates confidence score from dividing xy_support by x_support, then documents that score under [confidence, x + y]
def document_confidence(x, x_support, y, xy_support, confidence_list):
	# calculating confidence of X -> Y, using XY support / X support
	confidence = float(xy_support / x_support)
	confidence_list.append([confidence, x + y])


# Calculates and documents each pair's confidence score with the appropriate association rules, returns frequent pairs
def	pairs_confidence_and_freq(singles_count_d, pairs_count_a, n, pairs_confidence_list):
	freq_pairs = {}
	for item1 in freq_items:
		for item2 in freq_items:
			i = freq_items[item1]
			j = freq_items[item2]
			baskets_with_ij = pairs_count_a[int((i - 1) * (n - i / 2) + j - i)]
			if i < j and baskets_with_ij > 0:
				# confidence that {item1} -> {item2}
				document_confidence([item1], singles_count_d[item1], [item2], baskets_with_ij, pairs_confidence_list)
				# confidence that {item2} -> {item1}
				document_confidence([item2], singles_count_d[item2], [item1], baskets_with_ij, pairs_confidence_list)
				# if support is high enough for the pair, add to freq_pairs
				if baskets_with_ij >= SUPPORT:
					freq_pairs[(item1, item2)] = baskets_with_ij
					freq_pairs[(item2, item1)] = baskets_with_ij
	return freq_pairs


# Calculates and documents each triple's confidence score with the appropriate association rules
def triples_confidence(triples_count_d, freq_pairs):
	triples_confidence_list = []
	for triple in triples_count_d:
		baskets_with_all = triples_count_d[triple]
		association_list = get_combo(triple, 2)  # {X, Y, Z} -> {X, Y}, {X, Z}, {Y, Z}
		for rule in association_list:
			for item in triple:
				if item not in rule:  # {X, Y} -> Z, {X, Z} -> Y, {Y, Z} -> X
					document_confidence(rule, freq_pairs[(rule[0], rule[1])], [item], baskets_with_all, triples_confidence_list)
					break
	return triples_confidence_list


# Entry function for the A-Priori Algorithm
def main():
	# Get lines from file
	all_lines = read_input()
	# Parse lines
	parsed_lines = []
	for line in all_lines:
		parsed_lines.append(line.split())

	# Pass 1: Read baskets and count in main memory the occurrences of each item
	singles_count_d = pass_1(parsed_lines)
	# Find frequent items (items that appear more or equal to the value set to global variable SUPPORT)
	n = freq_item_count(singles_count_d)

	# Pass 2: Read baskets again and only count in main memory the pairs where both items are frequent
	pairs_count_a = pass_2(parsed_lines, n)

	# Get list of pairs confidence scores and freq_pairs
	pairs_confidence_list = []
	freq_pairs = pairs_confidence_and_freq(singles_count_d, pairs_count_a, n, pairs_confidence_list)

	# Pass 3: Read buckets again and only count in main memory the triples where all pairs of the 3 items are frequent
	triples_count_d = pass_3(parsed_lines, freq_pairs)

	# Get list of triples confidence scores
	triples_confidence_list = triples_confidence(triples_count_d, freq_pairs)

	# Sort both lists of confidence scores decreasingly, breaking any ties if needed to
	pairs_confidence_list.sort(key=lambda x: (-x[0], x[1][0], x[1][1]))
	triples_confidence_list.sort(key=lambda x: (-x[0], x[1][0], x[1][1]))

	# Print to file the results
	dump_output(pairs_confidence_list[:5], triples_confidence_list[:5])


if __name__ == '__main__':
	start_time = time.time()
	main()
	print("--- Program took %.6s seconds ---" % (time.time() - start_time))
	input("Enter to close")