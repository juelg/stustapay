import { TaxRate, selectTaxRateAll, useDeleteTaxRateMutation, useListTaxRatesQuery } from "@/api";
import { TaxRateRoutes } from "@/app/routes";
import { ListLayout } from "@/components";
import { useCurrentNode, useCurrentUserHasPrivilegeAtNode, useRenderNode } from "@/hooks";
import { Delete as DeleteIcon, Edit as EditIcon } from "@mui/icons-material";
import { DataGrid, GridActionsCellItem, GridColDef } from "@mui/x-data-grid";
import { Loading } from "@stustapay/components";
import { useOpenModal } from "@stustapay/modal-provider";
import * as React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

export const TaxRateList: React.FC = () => {
  const { t } = useTranslation();
  const { currentNode } = useCurrentNode();
  const navigate = useNavigate();
  const canManageTaxRatesAtNode = useCurrentUserHasPrivilegeAtNode(TaxRateRoutes.privilege);
  const openModal = useOpenModal();

  const { taxRates, isLoading } = useListTaxRatesQuery(
    { nodeId: currentNode.id },
    {
      selectFromResult: ({ data, ...rest }) => ({
        ...rest,
        taxRates: data ? selectTaxRateAll(data) : undefined,
      }),
    }
  );
  const [deleteTaxRate] = useDeleteTaxRateMutation();
  const renderNode = useRenderNode();

  if (isLoading) {
    return <Loading />;
  }

  const openConfirmDeleteDialog = (taxRateId: number) => {
    openModal({
      type: "confirm",
      title: t("deleteTaxRate"),
      content: t("deleteTaxRateDescription"),
      onConfirm: () => {
        deleteTaxRate({ nodeId: currentNode.id, taxRateId })
          .unwrap()
          .catch(() => undefined);
        return true;
      },
    });
  };

  const columns: GridColDef<TaxRate>[] = [
    {
      field: "name",
      headerName: t("taxRateName") as string,
      width: 100,
    },
    {
      field: "description",
      headerName: t("taxRateDescription") as string,
      flex: 1,
    },
    {
      field: "rate",
      headerName: t("taxRateRate") as string,
      align: "right",
      type: "number",
      valueGetter: (params) => params.row.rate * 100,
      valueFormatter: ({ value }) => `${value.toFixed(2)} %`,
    },
    {
      field: "node_id",
      headerName: t("common.definedAtNode") as string,
      valueFormatter: ({ value }) => renderNode(value),
      flex: 1,
    },
    {
      field: "actions",
      type: "actions",
      headerName: t("actions") as string,
      width: 150,
      getActions: (params) =>
        canManageTaxRatesAtNode(params.row.node_id)
          ? [
              <GridActionsCellItem
                icon={<EditIcon />}
                color="primary"
                label={t("edit")}
                onClick={() => navigate(TaxRateRoutes.edit(params.row.id))}
              />,
              <GridActionsCellItem
                icon={<DeleteIcon />}
                color="error"
                label={t("delete")}
                onClick={() => openConfirmDeleteDialog(params.row.id)}
              />,
            ]
          : [],
    },
  ];

  return (
    <ListLayout title={t("taxRates")} routes={TaxRateRoutes}>
      <DataGrid
        autoHeight
        getRowId={(row) => row.name}
        rows={taxRates ?? []}
        columns={columns}
        disableRowSelectionOnClick
        sx={{ p: 1, boxShadow: (theme) => theme.shadows[1] }}
      />
    </ListLayout>
  );
};
