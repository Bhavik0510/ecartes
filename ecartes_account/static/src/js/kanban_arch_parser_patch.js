/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { exprToBoolean } from "@web/core/utils/strings";
import { visitXML } from "@web/core/utils/xml";
import { SearchArchParser } from "@web/search/search_arch_parser";
import { stringToOrderBy } from "@web/search/utils/order_by";
import { Field } from "@web/views/fields/field";
import { FormArchParser } from "@web/views/form/form_arch_parser";
import {
    KANBAN_CARD_ATTRIBUTE,
    KanbanArchParser,
    LEGACY_KANBAN_BOX_ATTRIBUTE,
} from "@web/views/kanban/kanban_arch_parser";
import { ListArchParser } from "@web/views/list/list_arch_parser";
import { getActiveActions, processButton } from "@web/views/utils";
import { Widget } from "@web/views/widgets/widget";

/**
 * Remove <field name="…"/> nodes that are not in models[modelName].fields so arch parsers
 * never call Field.parseFieldNode / .type on missing definitions (merged Studio/legacy views).
 */
function stripUndefinedArchFields(xmlDoc, models, modelName) {
    const fieldMap = models[modelName]?.fields;
    if (!fieldMap) {
        return;
    }
    const SUBVIEW_TAGS = new Set(["list", "tree", "kanban", "graph", "pivot", "calendar", "activity"]);
    const isInsideSubview = (node) => {
        let current = node.parentNode;
        while (current) {
            if (current.tagName && SUBVIEW_TAGS.has(current.tagName)) {
                return true;
            }
            current = current.parentNode;
        }
        return false;
    };
    const toRemove = [];
    visitXML(xmlDoc, (node) => {
        if (node.tagName === "field") {
            // Nested one2many/many2many subviews use a different model, so their
            // fields must never be validated against the parent model field map.
            if (isInsideSubview(node)) {
                return;
            }
            const fname = node.getAttribute("name");
            if (fname && !fieldMap[fname]) {
                toRemove.push(node);
            }
        }
    });
    for (const node of toRemove) {
        node.parentNode?.removeChild(node);
    }
}

patch(FormArchParser.prototype, {
    parse(xmlDoc, models, modelName) {
        stripUndefinedArchFields(xmlDoc, models, modelName);
        return super.parse(xmlDoc, models, modelName);
    },
});

patch(ListArchParser.prototype, {
    parse(xmlDoc, models, modelName) {
        stripUndefinedArchFields(xmlDoc, models, modelName);
        return super.parse(xmlDoc, models, modelName);
    },
});

/**
 * Core KanbanArchParser reads models[model].fields[name].type before validating the
 * field exists; merged customer views can reference removed/optional fields and crash OWL.
 * Skip unknown field nodes instead of throwing.
 */
patch(KanbanArchParser.prototype, {
    parse(xmlDoc, models, modelName) {
        const fields = models[modelName].fields;
        const className = xmlDoc.getAttribute("class") || null;
        const canOpenRecords = exprToBoolean(xmlDoc.getAttribute("can_open"), true);
        let defaultOrder = stringToOrderBy(xmlDoc.getAttribute("default_order") || null);
        const defaultGroupBy = xmlDoc.getAttribute("default_group_by");
        const limit = xmlDoc.getAttribute("limit");
        const countLimit = xmlDoc.getAttribute("count_limit");
        const recordsDraggable = exprToBoolean(xmlDoc.getAttribute("records_draggable"), true);
        const groupsDraggable = exprToBoolean(xmlDoc.getAttribute("groups_draggable"), true);
        const activeActions = getActiveActions(xmlDoc);
        activeActions.archiveGroup = exprToBoolean(xmlDoc.getAttribute("archivable"), true);
        activeActions.createGroup = exprToBoolean(xmlDoc.getAttribute("group_create"), true);
        activeActions.deleteGroup = exprToBoolean(xmlDoc.getAttribute("group_delete"), true);
        activeActions.editGroup = exprToBoolean(xmlDoc.getAttribute("group_edit"), true);
        activeActions.quickCreate =
            activeActions.create && exprToBoolean(xmlDoc.getAttribute("quick_create"), true);
        const onCreate = xmlDoc.getAttribute("on_create");
        const quickCreateView = xmlDoc.getAttribute("quick_create_view");
        const tooltipInfo = {};
        let handleField = null;
        const fieldNodes = {};
        const fieldNextIds = {};
        const widgetNodes = {};
        let widgetNextId = 0;
        const jsClass = xmlDoc.getAttribute("js_class");
        const action = xmlDoc.getAttribute("action");
        const type = xmlDoc.getAttribute("type");
        const openAction = action && type ? { action, type } : null;
        const templateDocs = {};
        let headerButtons = [];
        const creates = [];
        let button_id = 0;
        visitXML(xmlDoc, (node) => {
            if (node.hasAttribute("t-name")) {
                templateDocs[node.getAttribute("t-name")] = node;
                return;
            }
            if (node.tagName === "header") {
                headerButtons = [...node.children]
                    .filter((n) => n.tagName === "button")
                    .map((n) => ({
                        ...processButton(n),
                        type: "button",
                        id: button_id++,
                    }))
                    .filter((button) => button.invisible !== "True" && button.invisible !== "1");
                return false;
            } else if (node.tagName === "control") {
                for (const childNode of node.children) {
                    if (childNode.tagName === "button") {
                        creates.push({
                            type: "button",
                            ...processButton(childNode),
                        });
                    } else if (childNode.tagName === "create") {
                        creates.push({
                            type: "create",
                            context: childNode.getAttribute("context"),
                            string: childNode.getAttribute("string"),
                        });
                    }
                }
                return false;
            }
            if (node.tagName === "field") {
                const fname = node.getAttribute("name");
                const fieldDef = fields[fname];
                if (!fieldDef) {
                    return false;
                }
                const widget = node.getAttribute("widget");
                if (!widget && fieldDef.type === "many2many") {
                    node.setAttribute("widget", "many2many_tags");
                }
                const fieldInfo = Field.parseFieldNode(node, models, modelName, "kanban", jsClass);
                const name = fieldInfo.name;
                if (!(fieldInfo.name in fieldNextIds)) {
                    fieldNextIds[fieldInfo.name] = 0;
                }
                const fieldId = `${fieldInfo.name}_${fieldNextIds[fieldInfo.name]++}`;
                fieldNodes[fieldId] = fieldInfo;
                node.setAttribute("field_id", fieldId);
                if (fieldInfo.options.group_by_tooltip) {
                    tooltipInfo[name] = fieldInfo.options.group_by_tooltip;
                }
                if (fieldInfo.isHandle) {
                    handleField = name;
                }
            }
            if (node.tagName === "widget") {
                const widgetInfo = Widget.parseWidgetNode(node);
                const widgetId = `widget_${++widgetNextId}`;
                widgetNodes[widgetId] = widgetInfo;
                node.setAttribute("widget_id", widgetId);
            }

            if (node.tagName === "img") {
                const attSrc = node.getAttribute("t-att-src");
                if (
                    attSrc &&
                    /\bkanban_image\b/.test(attSrc) &&
                    !Object.values(fieldNodes).some((f) => f.name === "write_date")
                ) {
                    fieldNodes.write_date_0 = { name: "write_date", type: "datetime" };
                }
            }
        });

        let progressAttributes = false;
        const progressBar = xmlDoc.querySelector("progressbar");
        if (progressBar) {
            progressAttributes = this.parseProgressBar(progressBar, fields);
        }

        let cardDoc = templateDocs[KANBAN_CARD_ATTRIBUTE];
        const isLegacyArch = !cardDoc;
        if (isLegacyArch) {
            console.warn("'kanban-box' is deprecated, define a 'card' template instead");
        }
        if (!cardDoc) {
            cardDoc = templateDocs[LEGACY_KANBAN_BOX_ATTRIBUTE];
            if (!cardDoc) {
                throw new Error(`Missing '${KANBAN_CARD_ATTRIBUTE}' template.`);
            }
        }
        const cardClassName = (!isLegacyArch && cardDoc.getAttribute("class")) || "";

        if (!defaultOrder.length && handleField) {
            const handleFieldSort = `${handleField}, id`;
            defaultOrder = stringToOrderBy(handleFieldSort);
        }

        return {
            activeActions,
            canOpenRecords,
            cardClassName,
            cardColorField: xmlDoc.getAttribute("highlight_color"),
            className,
            creates,
            defaultGroupBy,
            fieldNodes,
            widgetNodes,
            handleField,
            headerButtons,
            defaultOrder,
            onCreate,
            openAction,
            quickCreateView,
            recordsDraggable,
            groupsDraggable,
            limit: limit && parseInt(limit, 10),
            countLimit: countLimit && parseInt(countLimit, 10),
            progressAttributes,
            templateDocs,
            tooltipInfo,
            examples: xmlDoc.getAttribute("examples"),
            xmlDoc,
            isLegacyArch,
        };
    },
});

/**
 * SearchArchParser.visitFilter dereferences this.fields[fieldName].type for <filter date=""/>
 * without checking the field exists (e.g. merged search arch after a field was removed).
 */
patch(SearchArchParser.prototype, {
    visitFilter(node, visitChildren) {
        if (node.hasAttribute("date")) {
            const fieldName = node.getAttribute("date");
            if (!this.fields[fieldName]) {
                const clone = node.cloneNode(true);
                clone.removeAttribute("date");
                return super.visitFilter(clone, visitChildren);
            }
        }
        return super.visitFilter(node, visitChildren);
    },
});
