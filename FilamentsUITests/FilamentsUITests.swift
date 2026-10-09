import XCTest

final class FilamentsUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--ui-testing-reset"]
        if name.contains("testOwnedDiscontinuedEntryRemainsEditableAndReplacementStaysVisible") {
            app.launchArguments.append("--ui-testing-seed-discontinued")
        }
        if name.contains("testInstalledCatalogueUpgradePreservesInventoryAndMissingRecords") {
            app.launchArguments.append("--ui-testing-seed-upgrade")
        }
        if name.contains("testFailedCatalogueUpdateKeepsStoredCatalogueAndInventoryAvailable") {
            app.launchArguments += [
                "--ui-testing-seed-upgrade",
                "--ui-testing-fail-catalogue-update",
            ]
        }
        if name.contains("testInventorySaveFailureKeepsDraftAndDoesNotPersist") {
            app.launchArguments.append("--ui-testing-fail-inventory-save")
        }
        if name.contains("testVariedSwatchesHaveUsefulAccessibleDescriptions") {
            app.launchArguments.append("--ui-testing-seed-varied-swatches")
        }
        if name.contains("testCoreScreensPassAccessibilityAuditInDarkAppearance") {
            app.launchArguments.append("--ui-testing-dark-appearance")
        }
        if name.contains("testLibraryAtLargestAccessibilityTextSize") {
            app.launchArguments += [
                "-UIPreferredContentSizeCategoryName",
                "UICTContentSizeCategoryAccessibilityExtraExtraExtraLarge",
            ]
        }
        app.launch()
        XCTAssertTrue(app.navigationBars["Filaments"].waitForExistence(timeout: 5))
    }

    func testSpoolSelectionAppearsInInventoryAndSurvivesRelaunch() {
        openFilament("GFA00:10300")
        setToggleOn(app.switches["inventory.hasSpool"])
        app.buttons["Done"].tap()

        selectScope("Inventory")
        XCTAssertTrue(row("GFA00:10300").waitForExistence(timeout: 5))
        assertInventoryTotals(spools: 1, refills: 0)

        app.terminate()
        app.launchArguments = []
        app.launch()
        selectScope("Inventory")
        XCTAssertTrue(row("GFA00:10300").waitForExistence(timeout: 5))
        assertInventoryTotals(spools: 1, refills: 0)
    }

    func testInventoryTotalsFollowFiltersAndSearch() {
        openFilament("GFB00:40601")
        setToggleOn(app.switches["inventory.hasSpool"])
        setToggleOn(app.switches["inventory.hasRefill"])
        app.buttons["Done"].tap()

        scrollToElement(row("GFB01:45101"))
        openFilament("GFB01:45101")
        setToggleOn(app.switches["inventory.hasRefill"])
        app.buttons["Done"].tap()

        selectScope("Inventory")
        assertInventoryTotals(spools: 1, refills: 2)

        openFilters()
        setToggleOn(filterOption("ABS"))
        app.buttons["Done"].tap()
        assertInventoryTotals(spools: 1, refills: 1)

        setSearch("No matching filament")
        assertInventoryTotals(spools: 0, refills: 0)
    }

    func testInventorySaveFailureKeepsDraftAndDoesNotPersist() {
        openFilament("GFA00:10300")
        let spoolToggle = app.switches["inventory.hasSpool"]
        setToggleOn(spoolToggle)
        app.buttons["Done"].tap()

        let alert = app.alerts["Couldn't save inventory"]
        XCTAssertTrue(alert.waitForExistence(timeout: 3))
        XCTAssertTrue(alert.staticTexts.element(
            matching: NSPredicate(format: "label CONTAINS[c] %@", "weren't saved")
        ).exists)
        XCTAssertEqual(spoolToggle.value as? String, "1")
        alert.buttons["OK"].tap()
        XCTAssertTrue(spoolToggle.waitForExistence(timeout: 2))
        XCTAssertEqual(spoolToggle.value as? String, "1")

        app.terminate()
        app.launchArguments = []
        app.launch()
        XCTAssertTrue(app.navigationBars["Filaments"].waitForExistence(timeout: 5))
        selectScope("Inventory")
        XCTAssertTrue(row("GFA00:10300").waitForNonExistence(timeout: 2))
        XCTAssertTrue(app.descendants(matching: .any)["library.emptyState.title"].exists)
    }

    func testReplacementDoesNotImplyOwnership() {
        openFilament("GFA00:10300")
        setToggleOn(app.switches["inventory.needsReplacement"])
        app.buttons["Done"].tap()

        selectScope("Replace")
        XCTAssertTrue(row("GFA00:10300").waitForExistence(timeout: 5))

        selectScope("Inventory")
        XCTAssertTrue(row("GFA00:10300").waitForNonExistence(timeout: 2))
    }

    func testMaterialAndOwnershipFiltersCombine() {
        openFilament("GFA01:11502")
        setToggleOn(app.switches["inventory.hasRefill"])
        app.buttons["Done"].tap()

        openFilters()
        setToggleOn(filterOption("PLA"))
        setToggleOn(app.switches["Has refill"])
        app.buttons["Done"].tap()

        XCTAssertTrue(row("GFA01:11502").waitForExistence(timeout: 5))
        XCTAssertFalse(row("GFA00:10300").exists)
        XCTAssertFalse(row("GFG02:33102").exists)
    }

    func testMaterialVariantFilterCanBeCleared() {
        openFilters()
        setToggleOn(filterOption("PLA Matte"))
        app.buttons["Done"].tap()

        XCTAssertTrue(row("GFA01:11502").waitForExistence(timeout: 5))
        XCTAssertFalse(row("GFA00:10300").exists)

        openFilters()
        scrollToElement(app.buttons["Clear filters"])
        app.buttons["Clear filters"].tap()
        app.buttons["Done"].tap()
        XCTAssertTrue(row("GFA00:10300").waitForExistence(timeout: 5))
    }

    func testOwnedDiscontinuedEntryRemainsEditableAndReplacementStaysVisible() {
        let discontinuedRow = row("GFA00:10300")
        XCTAssertTrue(discontinuedRow.waitForExistence(timeout: 5))
        XCTAssertTrue(discontinuedRow.label.contains("Spool"))
        XCTAssertTrue(discontinuedRow.label.contains("Needs replacement"))
        XCTAssertTrue(discontinuedRow.label.contains("Discontinued"))

        openFilament("GFA00:10300")
        let explanation = elementWithLabel(containing: "no longer listed in the Australian catalogue")
        scrollToElement(explanation)
        XCTAssertTrue(explanation.exists)
        XCTAssertFalse(elementWithLabel(containing: "View on Bambu Lab AU").exists)
        setToggleOff(app.switches["inventory.hasSpool"])
        app.buttons["Done"].tap()

        selectScope("Inventory")
        XCTAssertTrue(discontinuedRow.waitForNonExistence(timeout: 3))
        selectScope("Replace")
        XCTAssertTrue(discontinuedRow.waitForExistence(timeout: 5))
        XCTAssertTrue(discontinuedRow.label.contains("Needs replacement"))
        XCTAssertTrue(discontinuedRow.label.contains("Discontinued"))
    }

    func testLibraryAtLargestAccessibilityTextSize() throws {
        let filamentRow = row("GFA00:10300")
        XCTAssertTrue(filamentRow.waitForExistence(timeout: 5))
        XCTAssertTrue(filamentRow.label.contains("Orange"))
        XCTAssertTrue(filamentRow.label.contains("PLA Basic"))
        XCTAssertTrue(filamentRow.label.contains("Solid colour"))

        try app.performAccessibilityAudit(for: [.dynamicType, .textClipped])

        filamentRow.tap()
        XCTAssertTrue(app.switches["inventory.hasSpool"].waitForExistence(timeout: 3))
        XCTAssertTrue(elementWithLabel(containing: "Orange, solid colour swatch").exists)
        try app.performAccessibilityAudit(for: .textClipped)
    }

    func testLibraryInLandscape() throws {
        XCUIDevice.shared.orientation = .landscapeLeft
        addTeardownBlock {
            XCUIDevice.shared.orientation = .portrait
        }

        XCTAssertTrue(app.navigationBars["Filaments"].waitForExistence(timeout: 5))
        XCTAssertTrue(row("GFA00:10300").waitForExistence(timeout: 5))
        XCTAssertTrue(app.segmentedControls.buttons["Inventory"].exists)
        try app.performAccessibilityAudit(for: .textClipped)
    }

    func testCoreScreensPassAccessibilityAudit() throws {
        try performAccessibilityAuditIgnoringSystemFormHeaders()

        openFilament("GFA00:10300")
        try performAccessibilityAuditIgnoringSystemFormHeaders(
            allowsUnattributedModalFindings: true
        )
    }

    func testCoreScreensPassAccessibilityAuditInDarkAppearance() throws {
        let aboutButton = app.buttons["library.about"]
        XCTAssertTrue(aboutButton.waitForExistence(timeout: 3))
        XCTAssertTrue(waitForValue("Dark appearance", on: aboutButton))
        try performAccessibilityAuditIgnoringSystemFormHeaders()

        openFilament("GFA00:10300")
        try performAccessibilityAuditIgnoringSystemFormHeaders(
            allowsUnattributedModalFindings: true
        )
    }

    func testVariedSwatchesHaveUsefulAccessibleDescriptions() {
        assertSwatch(
            key: "GFA00:10900",
            rowDescription: "Gradient colour",
            detailDescription: "Arctic Whisper, gradient colour swatch"
        )
        assertSwatch(
            key: "GFG01:32501",
            rowDescription: "Translucent colour",
            detailDescription: "Translucent Teal, translucent colour swatch"
        )
        assertSwatch(
            key: "UITEST:00001",
            rowDescription: "Multicolour",
            detailDescription: "Multicolour Test, multicolour swatch"
        )
    }

    func testAboutExplainsLocalDataAndAttribution() {
        app.buttons["library.about"].tap()
        XCTAssertTrue(app.navigationBars["About"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["about.independence"].exists)

        let localStorage = elementWithLabel(containing: "stored only on this device")
        scrollToElement(localStorage)
        XCTAssertTrue(localStorage.exists)

        let bundledCatalogue = elementWithLabel(containing: "doesn't fetch store listings or live stock")
        scrollToElement(bundledCatalogue)
        XCTAssertTrue(bundledCatalogue.exists)

        let sourceData = app.descendants(matching: .any)["about.sourceData"]
        scrollToElement(sourceData)
        XCTAssertTrue(sourceData.exists)

        let sourceLicence = app.descendants(matching: .any)["about.sourceLicence"]
        scrollToElement(sourceLicence)
        XCTAssertTrue(sourceLicence.exists)

        let catalogueVersion = elementWithLabel(containing: "2026.10.02.2")
        scrollToElement(catalogueVersion)
        XCTAssertTrue(catalogueVersion.exists)
    }

    func testDraftCatalogueNoticeIsAbsent() {
        XCTAssertFalse(app.descendants(matching: .any)["library.draftCatalogueNotice"].exists)
    }

    func testEmptyStatesExplainHowToRecover() {
        selectScope("Inventory")
        let emptyTitle = app.descendants(matching: .any)["library.emptyState.title"]
        let emptyDescription = app.descendants(matching: .any)["library.emptyState.description"]
        XCTAssertTrue(emptyTitle.waitForExistence(timeout: 3))
        XCTAssertEqual(emptyTitle.label, "No filaments")
        XCTAssertTrue(emptyDescription.waitForExistence(timeout: 3))
        XCTAssertTrue(emptyDescription.label.contains("mark as a spool or refill"))

        selectScope("All")
        let searchField = app.searchFields.firstMatch
        XCTAssertTrue(searchField.waitForExistence(timeout: 3))
        searchField.tap()
        searchField.typeText("No matching filament")

        XCTAssertTrue(emptyTitle.waitForExistence(timeout: 3))
        XCTAssertEqual(emptyTitle.label, "No results")
        XCTAssertTrue(emptyDescription.waitForExistence(timeout: 3))
        XCTAssertTrue(emptyDescription.label.contains("changing the search or filters"))
    }

    func testInstalledCatalogueUpgradePreservesInventoryAndMissingRecords() {
        let updatedRow = row("GFA00:10300")
        XCTAssertTrue(updatedRow.waitForExistence(timeout: 5))
        XCTAssertTrue(updatedRow.label.contains("Orange"))
        XCTAssertFalse(updatedRow.label.contains("Legacy Orange"))
        XCTAssertTrue(updatedRow.label.contains("Spool"))
        XCTAssertTrue(updatedRow.label.contains("Refill"))
        XCTAssertTrue(updatedRow.label.contains("Needs replacement"))

        openFilament("GFA00:10300")
        XCTAssertEqual(app.switches["inventory.hasSpool"].value as? String, "1")
        XCTAssertEqual(app.switches["inventory.hasRefill"].value as? String, "1")
        XCTAssertEqual(app.switches["inventory.needsReplacement"].value as? String, "1")
        XCTAssertTrue(elementWithLabel(containing: "Orange, solid colour swatch").exists)
        app.buttons["Done"].tap()

        let retainedRow = row("LEGACY:99999")
        XCTAssertTrue(retainedRow.waitForExistence(timeout: 5))
        XCTAssertTrue(retainedRow.label.contains("Legacy Blue"))
        XCTAssertTrue(retainedRow.label.contains("Refill"))
        XCTAssertTrue(retainedRow.label.contains("Needs replacement"))

        openFilament("LEGACY:99999")
        XCTAssertEqual(app.switches["inventory.hasRefill"].value as? String, "1")
        XCTAssertEqual(app.switches["inventory.needsReplacement"].value as? String, "1")
        let reviewNeeded = elementWithLabel(containing: "Review needed")
        scrollToElement(reviewNeeded)
        XCTAssertTrue(reviewNeeded.exists)
    }

    func testFailedCatalogueUpdateKeepsStoredCatalogueAndInventoryAvailable() {
        let issue = app.descendants(matching: .any)["library.catalogueIssue"]
        XCTAssertTrue(issue.waitForExistence(timeout: 3))
        XCTAssertTrue(issue.label.contains("saved catalogue and inventory are unchanged"))

        let retainedRow = row("GFA00:10300")
        XCTAssertTrue(retainedRow.waitForExistence(timeout: 5))
        XCTAssertTrue(retainedRow.label.contains("Legacy Orange"))
        XCTAssertTrue(retainedRow.label.contains("Spool"))
        XCTAssertTrue(retainedRow.label.contains("Refill"))
        XCTAssertTrue(retainedRow.label.contains("Needs replacement"))

        selectScope("Inventory")
        XCTAssertTrue(retainedRow.waitForExistence(timeout: 3))
        XCTAssertTrue(row("LEGACY:99999").waitForExistence(timeout: 3))

        openFilament("GFA00:10300")
        XCTAssertEqual(app.switches["inventory.hasSpool"].value as? String, "1")
        XCTAssertEqual(app.switches["inventory.hasRefill"].value as? String, "1")
        XCTAssertEqual(app.switches["inventory.needsReplacement"].value as? String, "1")
    }

    private func openFilament(_ key: String) {
        let filamentRow = row(key)
        XCTAssertTrue(filamentRow.waitForExistence(timeout: 3))
        filamentRow.tap()
        let spoolToggle = app.switches["inventory.hasSpool"]
        if !spoolToggle.waitForExistence(timeout: 3) {
            XCTAssertTrue(filamentRow.waitForExistence(timeout: 2))
            filamentRow.tap()
        }
        XCTAssertTrue(spoolToggle.waitForExistence(timeout: 5))
    }

    private func assertSwatch(
        key: String,
        rowDescription: String,
        detailDescription: String
    ) {
        let filamentRow = row(key)
        XCTAssertTrue(filamentRow.waitForExistence(timeout: 5))
        XCTAssertTrue(filamentRow.label.contains(rowDescription))
        openFilament(key)
        XCTAssertTrue(elementWithLabel(containing: detailDescription).exists)
        app.buttons["Done"].tap()
        XCTAssertTrue(app.navigationBars["Filaments"].waitForExistence(timeout: 3))
    }

    private func row(_ key: String) -> XCUIElement {
        app.buttons["filament.row.\(key)"]
    }

    private func assertInventoryTotals(spools: Int, refills: Int) {
        let totals = app.staticTexts["library.inventoryTotals"]
        XCTAssertTrue(totals.waitForExistence(timeout: 3))
        XCTAssertEqual(totals.label, "Spools: \(spools), Refills: \(refills)")
    }

    private func setSearch(_ text: String) {
        let searchField = app.searchFields.firstMatch
        XCTAssertTrue(searchField.waitForExistence(timeout: 3))
        let current = searchField.value as? String ?? ""
        let enteredText = current == "Search filaments" ? "" : current
        searchField.tap()
        searchField.typeText(
            String(repeating: XCUIKeyboardKey.delete.rawValue, count: enteredText.count) + text
        )
    }

    private func elementWithLabel(containing text: String) -> XCUIElement {
        app.descendants(matching: .any)
            .matching(NSPredicate(format: "label CONTAINS[c] %@", text))
            .firstMatch
    }

    private func selectScope(_ name: String) {
        let scope = app.segmentedControls.buttons[name]
        XCTAssertTrue(scope.waitForExistence(timeout: 2))
        scope.tap()
    }

    private func openFilters() {
        app.buttons["library.filters"].tap()
        XCTAssertTrue(app.navigationBars["Filters"].waitForExistence(timeout: 3))
    }

    private func filterOption(_ value: String) -> XCUIElement {
        let option = app.switches.matching(identifier: "filter.option.\(value)").firstMatch
        scrollToElement(option)
        return option
    }

    private func scrollToElement(_ element: XCUIElement) {
        for _ in 0..<5 where !element.exists {
            app.swipeUp()
        }
        XCTAssertTrue(element.waitForExistence(timeout: 2))
    }

    private func setToggleOn(_ toggle: XCUIElement) {
        XCTAssertTrue(toggle.waitForExistence(timeout: 2))
        if toggle.value as? String != "1" {
            toggle.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)).tap()
        }
        XCTAssertTrue(waitForValue("1", on: toggle))
    }

    private func setToggleOff(_ toggle: XCUIElement) {
        XCTAssertTrue(toggle.waitForExistence(timeout: 2))
        if toggle.value as? String != "0" {
            toggle.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)).tap()
        }
        XCTAssertTrue(waitForValue("0", on: toggle))
    }

    private func waitForValue(_ value: String, on element: XCUIElement) -> Bool {
        let predicate = NSPredicate(format: "value == %@", value)
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        return XCTWaiter.wait(for: [expectation], timeout: 2) == .completed
    }

    private func performAccessibilityAuditIgnoringSystemFormHeaders(
        allowsUnattributedModalFindings: Bool = false
    ) throws {
        let systemStyledLabels: Set<String> = [
            "About Filaments",
            "Availability",
            "Bundled catalogue",
            "Catalogue",
            "Catalogue sources",
            "Done",
            "Inventory",
            "Material families",
            "Material variants",
            "My inventory",
            "Your data",
        ]

        try app.performAccessibilityAudit { issue in
            // Xcode can report the system-rendered iPad sheet presentation without
            // an element. The largest-text test audits the detail content separately.
            if (
                issue.auditType == .contrast
                    || issue.auditType == .elementDetection
                    || issue.auditType == .dynamicType
            ),
               issue.element == nil,
               allowsUnattributedModalFindings {
                return true
            }
            // SwiftUI owns the styling and scaling of these Form headers and the
            // confirmation button. App-controlled text isn't included here.
            guard issue.auditType == .contrast || issue.auditType == .dynamicType else {
                return false
            }
            guard let label = issue.element?.label else { return false }
            return systemStyledLabels.contains(label)
        }
    }
}
